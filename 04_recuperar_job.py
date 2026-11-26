"""Recupera el resultado de un job ya enviado a IBM Quantum.

Util si cerraste la terminal mientras el job esperaba en la cola. Los Job IDs
quedan anotados en resultados/job_ids.txt.

Uso:
    python 04_recuperar_job.py <JOB_ID>          -> job del estado de Bell (02)
    python 04_recuperar_job.py <JOB_ID> --ghz    -> job del GHZ (03), normaliza y grafica
"""

import argparse
import sys
from pathlib import Path

import matplotlib.pyplot as plt
from qiskit_ibm_runtime import QiskitRuntimeService

parser = argparse.ArgumentParser(description="Recuperar resultado de un job de IBM Quantum")
parser.add_argument("job_id")
parser.add_argument("--ghz", action="store_true", help="el job es del script 03 (GHZ)")
args = parser.parse_args()

RESULTADOS = Path(__file__).parent / "resultados"
RESULTADOS.mkdir(exist_ok=True)

service = QiskitRuntimeService()
job = service.job(args.job_id)
status = job.status()
print(f"Job {args.job_id} | backend: {job.backend().name} | estado: {status}")

if status in ("QUEUED", "INITIALIZING", "VALIDATING", "RUNNING"):
    sys.exit("El job aun no termina. Vuelve a ejecutar este script mas tarde.")
if status in ("ERROR", "CANCELLED"):
    sys.exit(f"El job termino con estado {status}: {job.error_message()}")

pub_result = job.result()[0]
data = pub_result.data
if not hasattr(data, "evs"):
    print("El resultado no tiene 'evs'; contenido crudo:")
    print(pub_result)
    sys.exit(0)

values = list(data.evs)
errors = list(data.stds) if hasattr(data, "stds") else [float("nan")] * len(values)

fig = plt.figure()
if args.ghz:
    norm = [v / values[0] for v in values]
    distancias = list(range(1, len(norm) + 1))
    for d, v in zip(distancias, norm):
        print(f"distancia {d:>3}: {v:.4f}")
    plt.plot(distancias, norm, marker="o", label=f"{len(norm) + 1}-qubit GHZ state")
    plt.xlabel("Distance between qubits $i$")
    plt.ylabel(r"$\langle Z_i Z_0 \rangle / \langle Z_1 Z_0 \rangle $")
    plt.legend()
else:
    labels = ["IZ", "IX", "ZI", "XI", "ZZ", "XX"]
    if len(labels) != len(values):
        labels = [str(i) for i in range(len(values))]
    for lbl, v, e in zip(labels, values, errors):
        print(f"{lbl:<6} {v:>7.4f} +/- {e:.4f}")
    plt.plot(labels, values, "-o")
    plt.xlabel("Observables")
    plt.ylabel("Values")

plt.title(f"Job {args.job_id} - {job.backend().name}")
ruta = RESULTADOS / f"04_job_{args.job_id}.png"
fig.savefig(ruta, bbox_inches="tight")
print(f"  figura guardada: {ruta}")
plt.show()
