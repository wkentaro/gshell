import subprocess


def check_output(cmd, retry=50):
    for _ in range(retry + 1):
        popen = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
        popen.wait()

        stdout = popen.stdout.read()
        if popen.returncode == 0:
            break
    if popen.returncode != 0:
        raise subprocess.CalledProcessError(
            returncode=popen.returncode,
            cmd=cmd,
            output=stdout,
        )
    if isinstance(stdout, bytes):
        stdout = stdout.decode('utf-8')
    return stdout
