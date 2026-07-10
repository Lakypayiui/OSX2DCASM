import os
import sys
from multiprocessing import freeze_support, set_start_method
import multiprocessing as mp
from acosxm import ACOSXM
if "main" in sys.modules or getattr(sys, 'frozen', False):
    os.environ.setdefault('MAIN_PID', str(os.getpid()))

if __name__ == "__main__":
    freeze_support()
    mp.set_start_method("spawn", force=True)
    
    print(f"=== PROCESO PRINCIPAL INICIADO PID = {os.getpid()} ===")
    

    
    ACOSXM().run()