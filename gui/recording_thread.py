import threading
import time
import pathlib
import sys
import multiprocessing


sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))


def _joystick_process(mp_queue, stop_event, base_dir_str):
    """Runs in a child process — owns pygame entirely, no SDL conflicts."""
    import time
    import sys
    import pathlib
    sys.path.insert(0, base_dir_str)
    from analyzer import Analyzer

    try:
        import pygame
    except ImportError:
        mp_queue.put(("error", "pygame is not installed"))
        return

    try:
        pygame.init()
        pygame.joystick.init()
    except Exception as e:
        mp_queue.put(("error", f"pygame init failed: {e}"))
        return

    if pygame.joystick.get_count() == 0:
        mp_queue.put(("error", "No controller detected. Plug in your controller and try again."))
        pygame.quit()
        return

    try:
        joystick = pygame.joystick.Joystick(0)
        joystick.init()
        mp_queue.put(("controller", joystick.get_name()))
    except Exception as e:
        mp_queue.put(("error", f"Could not init joystick: {e}"))
        pygame.quit()
        return

    try:
        ana = Analyzer(base_dir=pathlib.Path(base_dir_str))
    except Exception as e:
        mp_queue.put(("error", f"Could not load mapping files: {e}"))
        pygame.quit()
        return

    ana.on_chat_recognized = lambda msg: mp_queue.put(("chat", msg))

    recorded_path = str(pathlib.Path(base_dir_str) / "recorded.txt")
    last_hats = [(0, 0)]
    time_saved = time.time()
    time_changed = time.time()

    while not stop_event.is_set():
        try:
            pygame.event.pump()
            num_hats = joystick.get_numhats()
            hats = [joystick.get_hat(i) for i in range(num_hats)]

            if hats and hats != last_hats and hats != [(0, 0)]:
                ana.add(hats)
                time_changed = time.time()
            last_hats = hats

            now = time.time()
            if now - time_changed > 10 and now - time_saved > 20:
                ana.save_recorded(recorded_path)
                mp_queue.put(("autosave", None))
                time_saved = now

        except Exception as e:
            mp_queue.put(("error", f"Recording error: {e}"))
            break

        time.sleep(0.01)

    try:
        ana.save_recorded(recorded_path)
    except Exception:
        pass

    mp_queue.put(("stopped", None))

    try:
        pygame.quit()
    except Exception:
        pass


class RecordingThread(threading.Thread):
    """
    Thin thread that owns a child process running the pygame joystick loop.
    The child process has its own SDL context so it doesn't conflict with
    tkinter's win32 message loop.
    """

    def __init__(self, message_queue, stop_event, base_dir):
        super().__init__(daemon=True)
        self._tk_queue = message_queue          # queue.Queue for tkinter tab
        self._stop_event = stop_event           # threading.Event
        self._base_dir = str(pathlib.Path(base_dir))

    def run(self):
        mp_manager = multiprocessing.Manager()
        mp_queue = mp_manager.Queue()
        mp_stop = mp_manager.Event()

        proc = multiprocessing.Process(
            target=_joystick_process,
            args=(mp_queue, mp_stop, self._base_dir),
            daemon=True,
        )
        proc.start()

        # Forward messages from the child process to the tkinter queue
        while proc.is_alive() or not mp_queue.empty():
            try:
                msg = mp_queue.get(timeout=0.1)
                self._tk_queue.put(msg)
                if msg[0] in ("stopped", "error"):
                    break
            except Exception:
                pass

            # Propagate stop signal from tkinter to the child process
            if self._stop_event.is_set() and not mp_stop.is_set():
                mp_stop.set()

        proc.join(timeout=5)
        if proc.is_alive():
            proc.terminate()
