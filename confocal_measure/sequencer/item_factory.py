def item_factory(measure, item_type, **kwargs):
    from .types.dir_operations import NewDir, SaveDirToParent
    from .types.exec_function import Function
    from .types.interrupt_if import InterruptIf
    from .item import Item
    from .types.iterations import EndIteration, StartIteration
    from .types.pause import Pause
    from .types.read_from_hardware import ReadFromHardWare
    from .types.run_measurement import RunMeasurement
    from .types.timeout import Timeout
    from .types.update_settings import UpdateSetting
    from .types.wait_until import WaitUntil

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
