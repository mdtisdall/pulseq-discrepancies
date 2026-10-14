"""Reads v131_rf.seq and v141_rf.seq (in the current folder) with
Sequence.read, then writes each with Sequence.write, first with the default
detect_rf_use=False, then with detect_rf_use=True."""
import traceback
import warnings

import pypulseq as pp

warnings.simplefilter('ignore')
for f in ['v131_rf.seq', 'v141_rf.seq']:
    for detect in [False, True]:
        seq = pp.Sequence()
        seq.read(f, detect_rf_use=detect)
        out = f.replace('.seq', f'_pypulseq_detect{int(detect)}.seq')
        print(f'{f} detect_rf_use={detect}: read; rf_library.type = {dict(seq.rf_library.type)}')
        try:
            seq.write(out)
            print(f'  write {out}: ok')
        except Exception:
            print(f'  write {out}: ' + traceback.format_exc(limit=-1).strip().splitlines()[-1])
