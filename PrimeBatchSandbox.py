from time import time as tm
from multiprocessing import Process, Manager
from time import sleep
from os import chdir, path, listdir

BATCHFOLDER = 'batch_primes'
PREFIX = 'PrimesTo_'
SAVESTRIDE = 500000  # re-build the files before changing, or nothing will load.
SUFFIX = '.txt'
SAVEINTERVAL = 10  # seconds
BATCHMASK = 3000  # no work on batches below this number
NUMTHREADS = 12  # Number of threads to spawn


STRIDESHARDS = NUMTHREADS * 2 # how many pieces to break each batch into for processing
SHARDLEN = ((SAVESTRIDE//STRIDESHARDS)//2)*2


def loadbatch(cur_batch):
    cur_limit = (cur_batch + 1) * SAVESTRIDE
    savefile = f'{BATCHFOLDER}/{PREFIX}{cur_limit}{SUFFIX}'
    try:
        f = open(savefile, "r")
        prime_source = f.read()
        f.close()
        loadedprimes = sorted([int(p) for p in prime_source.split() if p.isnumeric()])
        return True, loadedprimes
    except:
        return False, [0]


def load_all_batches():
    # dir_path = path.dirname(path.realpath(__file__))
    # dir_path = path.join(dir_path, BATCHFOLDER)
    # chdir(dir_path)
    # thesefiles = listdir()
    prime_digit_count = {0:0,1:0,2:0,3:0,4:0,5:0,6:0,7:0,8:0,9:0}
    for i in range(2000):
        cur_limit = (i + 1) * SAVESTRIDE
        savefile = f'{BATCHFOLDER}/{PREFIX}{cur_limit}{SUFFIX}'
        try:
            f = open(savefile, "r")
            prime_source = f.read()
            f.close()
            loadedprimes = [p for p in prime_source.split() if p.isnumeric()]
        except:
            return False, [0]
        for p in loadedprimes:
            prime_digit_count[len(p)] += 1

    return True, prime_digit_count

def isprime(candidate, primes):
    for factor in primes:
        if (candidate / factor) < factor: return True
        if candidate % factor == 0: return False
    raise  # because we should never get here


def findprimes(foundationprimes, newprimes: list, start_candidate, end_of_search):
    candidate = start_candidate
    while candidate < end_of_search:  # prime finder loop
        if isprime(candidate, foundationprimes):
            newprimes.append(candidate)
        candidate += 2


def prime_main():
    mngr = Manager()
    newprimes = mngr.list()
    loadsuccess, baseprimes = loadbatch(0)
    if loadsuccess:
        numinitprm = len(baseprimes)
        print(f'initial batch of {numinitprm} primes loaded')
    else:
        print('unable to load first batch of primes')
        print('bootstrapping not yet implemented')
        return False
    if baseprimes.pop(0) == 2:
        print('2 successfully excised')
    else:
        print('Initial Prime Corrupted')
        print('Revalidate data\nABORT!\nABORT!\nABORT!')
        return False
    cur_batch = BATCHMASK - 1
    while True:
        cur_batch += 1
        if cur_batch > 8590: break
        cur_limit = (cur_batch + 1) * SAVESTRIDE
        savefile = f'{BATCHFOLDER}/{PREFIX}{cur_limit}{SUFFIX}'
        loaded, loadedprimes = loadbatch(cur_batch)
        if loaded:
            shardstrt = loadedprimes[-1] + 2
        else:  # The current batch was not loaded, so init from the batch number
            shardstrt = cur_batch * SAVESTRIDE
            if shardstrt % 2 == 0: shardstrt += 1
        del loadedprimes
        processes = []
        savetm: float = tm() + SAVEINTERVAL
        shardend = shardstrt
        lastsavestart = shardstrt

        def saveit(primestosave, processestowait):
            while len(processestowait):
                processestowait.pop(0).join()
            sortedprimes = primestosave[:]
            sortedprimes.sort()
            curtm = tm()
            elapsed = curtm - savetm + SAVEINTERVAL
            numnewprimes = len(primestosave)
            numproced = shardend - lastsavestart
            print(f'saved {numnewprimes} from {numproced} numbers in {elapsed:>6.2f} seconds')
            f = open(savefile, "a")
            for i in sortedprimes:
                f.write(str(i) + '\n')
            f.close()
            return mngr.list()

        while shardend < cur_limit:  # prime finder thread management
            if len(processes) < NUMTHREADS:
                shardend = min(shardstrt + SHARDLEN, cur_limit)
                _prcs = Process(target=findprimes, args=(baseprimes, newprimes, shardstrt, shardend))
                processes.append(_prcs)
                _prcs.start()
                shardstrt = min(shardstrt + SHARDLEN, cur_limit-1)
            p = processes.pop(0)
            if p.is_alive(): processes.append(p)
            curtm = tm()
            if curtm > savetm:
                newprimes = saveit(newprimes, processes)
                savetm: float = tm() + SAVEINTERVAL
                lastsavestart = shardend + 2
        newprimes = saveit(newprimes, processes)
        print(f'Primes in batch {cur_batch} completed')


if __name__ == '__main__':
    loadsuccess, primecounts = load_all_batches()
    print(primecounts)
