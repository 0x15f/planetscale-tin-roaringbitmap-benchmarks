"""Finish an already-running standard job, then execute follow-ups serially."""
import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime,timezone
from pathlib import Path
from harness.audit import audit


def alive(pid):
    try:os.kill(pid,0);return True
    except ProcessLookupError:return False


def main():
    ap=argparse.ArgumentParser();ap.add_argument('standard');ap.add_argument('--primary-pid',type=int,required=True);args=ap.parse_args()
    standard=Path(args.standard);state_path=standard/'schedule.json'
    state={'status':'waiting_for_standard','started_at':datetime.now(timezone.utc).isoformat(),'standard':str(standard),'stages':[]}
    def save():state_path.write_text(json.dumps(state,indent=2))
    def stage(module,*arguments):
        state['status']=module;save();print('Starting',module,flush=True)
        before=set(Path('results').glob('*'))
        subprocess.run([sys.executable,'-m',module,*map(str,arguments)],check=True)
        created=[p for p in set(Path('results').glob('*'))-before if p.is_dir()]
        state['stages'].append({'module':module,'finished_at':datetime.now(timezone.utc).isoformat(),'artifacts':[str(p) for p in sorted(created)]});save()
        return created
    save()
    try:
        while json.loads((standard/'manifest.json').read_text())['status']!='complete':
            if not alive(args.primary_pid):
                # Preserve incomplete evidence; the agent must inspect the failure before retrying.
                raise RuntimeError('Primary benchmark process exited before completing; use the documented resume command after inspection')
            time.sleep(10)
        audit(standard)
        control=stage('harness.bitmap_control',standard)
        assert len(control)==1,'Expected one bitmap representation control run'
        concurrency=stage('harness.concurrency',standard)
        assert len(concurrency)==1,'Expected one concurrency run'
        scale=stage('harness.focused_scale',standard)
        assert len(scale)==1,'Expected one scale run'
        stage('harness.package_report',standard,'--concurrency',concurrency[0],'--scale',scale[0],'--bitmap-control',control[0])
        state['status']='complete';state['finished_at']=datetime.now(timezone.utc).isoformat();save()
        print('FULL SCHEDULE COMPLETE',flush=True)
    except Exception as exc:
        state.update(status='failed',error_type=type(exc).__name__,error=str(exc));save();raise

if __name__=='__main__':main()
