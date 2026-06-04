from multiprocessing import freeze_support, set_start_method
from acosxm import ACOSXM

if __name__ == "__main__":
    freeze_support()
    set_start_method("spawn")

    ACOSXM().run()