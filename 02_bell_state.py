"""Parte 1 del tutorial - Estado de Bell en una computadora cuantica.

Sigue los 4 pasos de Qiskit patterns:
  1. Mapear el problema a circuitos y observables
  2. Optimizar (transpilar) para el hardware
  3. Ejecutar con el primitivo Estimator
  4. Post-procesar y graficar

Uso:
    python 02_bell_state.py              -> simulador local con ruido (FakeBelemV2), sin cuenta
    python 02_bell_state.py --hardware   -> computadora cuantica real de IBM (necesita 01_guardar_cuenta.py)

Resultado esperado: <ZZ> y <XX> cercanos a 1 y los observables de un solo
qubit (IZ, IX, ZI, XI) cercanos a 0, porque los dos qubits estan entrelazados.
"""

import argparse
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
from qiskit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_ibm_runtime.executor_estimator import Estimator

parser = argparse.ArgumentParser(description="Estado de Bell (tutorial Hello world de IBM Quantum)")
parser.add_argument("--hardware", action="store_true", help="ejecutar en una QPU real de IBM")
args = parser.parse_args()
modo = "hardware" if args.hardware else "simulador"

RESULTADOS = Path(__file__).parent / "resultados"
RESULTADOS.mkdir(exist_ok=True)


def guardar(fig, nombre):
    ruta = RESULTADOS / nombre
    fig.savefig(ruta, bbox_inches="tight")
    plt.close(fig)
    print(f"  figura guardada: {ruta}")


# --- Paso 1: Mapear el problema a un circuito cuantico y observables ---------
qc = QuantumCircuit(2)
qc.h(0)
qc.cx(0, 1)
print(qc.draw("text"))
guardar(qc.draw("mpl"), "02_bell_circuito.png")

observables_labels = ["IZ", "IX", "ZI", "XI", "ZZ", "XX"]
observables = [SparsePauliOp(label) for label in observables_labels]

# --- Paso 2: Optimizar para el hardware -------------------------------------
if args.hardware:
    from qiskit_ibm_runtime import QiskitRuntimeService

    service = QiskitRuntimeService()
    backend = service.least_busy(simulator=False, operational=True)
else:
    from qiskit_ibm_runtime.fake_provider import FakeBelemV2

    backend = FakeBelemV2()
print(f"Backend ({modo}): {backend.name}")

pm = generate_preset_pass_manager(backend=backend, optimization_level=1)
isa_circuit = pm.run(qc)
guardar(isa_circuit.draw("mpl", idle_wires=False), f"02_bell_circuito_isa_{modo}.png")

mapped_observables = [observable.apply_layout(isa_circuit.layout) for observable in observables]

# --- Paso 3: Ejecutar con el Estimator --------------------------------------
estimator = Estimator(mode=backend)
estimator.options.resilience_level = 1
estimator.options.default_shots = 5000

job = estimator.run([(isa_circuit, mapped_observables)])
job_id = job.job_id()
print(f">>> Job ID: {job_id}")
if args.hardware:
    with open(RESULTADOS / "job_ids.txt", "a", encoding="utf-8") as f:
        f.write(f"{datetime.now():%Y-%m-%d %H:%M}  bell  {backend.name}  {job_id}\n")
    print("Esperando resultado (puede tardar si hay cola). Si cierras la terminal,")
    print(f"recuperalo luego con:  python 04_recuperar_job.py {job_id}")

# --- Paso 4: Post-procesar ---------------------------------------------------
pub_result = job.result()[0]
values = pub_result.data.evs
errors = pub_result.data.stds

lineas = [f"Backend: {backend.name} ({modo})", f"Job ID: {job_id}", "", "Observable   Valor     Error"]
lineas += [f"{lbl:<12} {v:>7.4f}   {e:.4f}" for lbl, v, e in zip(observables_labels, values, errors)]
texto = "\n".join(lineas)
print(texto)
(RESULTADOS / f"02_bell_valores_{modo}.txt").write_text(texto + "\n", encoding="utf-8")

fig = plt.figure()
plt.plot(observables_labels, values, "-o")
plt.xlabel("Observables")
plt.ylabel("Values")
plt.title(f"Estado de Bell - {backend.name} ({modo})")
fig.savefig(RESULTADOS / f"02_bell_resultado_{modo}.png", bbox_inches="tight")
print(f"  figura guardada: {RESULTADOS / f'02_bell_resultado_{modo}.png'}")
plt.show()
