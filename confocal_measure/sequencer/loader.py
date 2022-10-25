


def new_item(measure, item_type, **kwargs):
    from .dir_operations import NewDir, SaveDirToParent
    from .exec_function import Function
    from .interrupt_if import InterruptIf
    from .iterations import EndIteration, StartIteration
    from .list_items import Item
    from .pause import Pause
    from .read_from_hardware import ReadFromHardWare
    from .run_measurement import RunMeasurement
    from .timeout import Timeout
    from .update_settings import UpdateSetting
    from .wait_until import WaitUntil

    return {
        'update-setting': UpdateSetting,
        'read_from_hardware': ReadFromHardWare,
        'measurement': RunMeasurement,
        'wait-until': WaitUntil,
        'interrupt-if': InterruptIf,
        'timeout': Timeout,
        'function': Function,
        'pause': Pause,
        'new_dir': NewDir,
        'save_dir_to_parent': SaveDirToParent,
        'end-iteration': EndIteration,
        'start-iteration': StartIteration,
    }[item_type](measure, **kwargs)