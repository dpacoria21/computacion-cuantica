"""Parte 2 del tutorial - Estado GHZ de n qubits (escalar a 100 qubits).

Prepara un estado GHZ de n qubits y mide <Z_0 Z_i> para cada distancia i.
En un equipo ideal todos valdrian 1; en hardware real el ruido hace que la
correlacion decaiga con la distancia.

Uso:
    python 03_ghz_100_qubits.py              -> simulador local, n=10 (FakeGuadalupeV2, 16 qubits)
    python 03_ghz_100_qubits.py --hardware   -> QPU real de IBM, n=100 (como en el tutorial)
    python 03_ghz_100_qubits.py --hardware --n 50   -> elegir otro n

Nota: 100 qubits no se pueden simular en una PC, por eso el modo simulador usa n=10.
"""

import argparse
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
from qiskit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_ibm_runtime.executor_estimator import Estimator
from qiskit_ibm_runtime.options_models import EstimatorOptions

parser = argparse.ArgumentParser(description="Estado GHZ de n qubits (tutorial Hello world de IBM Quantum)")
parser.add_argument("--hardware", action="store_true", help="ejecutar en una QPU real de IBM")
parser.add_argument("--n", type=int, default=None, help="numero de qubits (por defecto 100 en hardware, 10 en simulador)")
args = parser.parse_args()
modo = "hardware" if args.hardware else "simulador"
n = args.n or (100 if args.hardware else 10)

RESULTADOS = Path(__file__).parent / "resultados"
RESULTADOS.mkdir(exist_ok=True)


# --- Paso 1: Mapear el problema a circuitos y operadores ---------------------
def get_qc_for_n_qubit_GHZ_state(n: int) -> QuantumCircuit:
    """Devuelve un QuantumCircuit que prepara el estado GHZ de n qubits."""
    if isinstance(n, int) and n >= 2:
        qc = QuantumCircuit(n)
        qc.h(0)
        for i in range(n - 1):
            qc.cx(i, i + 1)
    else:
        raise Exception("n no es un entero valido (debe ser >= 2)")
    return qc


qc = get_qc_for_n_qubit_GHZ_state(n)

# Operadores ZZII...I, ZIZI...I, ..., ZIII...Z  (n-1 operadores)
operator_strings = ["Z" + "I" * i + "Z" + "I" * (n - 2 - i) for i in range(n - 1)]
print(f"n = {n} qubits, {len(operator_strings)} operadores")
print("Primeros operadores:", operator_strings[:3], "...")
operators = [SparsePauliOp(op) for op in operator_strings]

# --- Paso 2: Optimizar para el hardware -------------------------------------
if args.hardware:
    from qiskit_ibm_runtime import QiskitRuntimeService

    service = QiskitRuntimeService()
    backend = service.least_busy(simulator=False, operational=True, min_num_qubits=n)
else:
    from qiskit_ibm_runtime.fake_provider import FakeGuadalupeV2

    backend = FakeGuadalupeV2()
    if n > backend.num_qubits:
        raise SystemExit(f"El simulador tiene {backend.num_qubits} qubits; usa --n <= {backend.num_qubits}")
print(f"Backend ({modo}): {backend.name} ({backend.num_qubits} qubits)")

pm = generate_preset_pass_manager(optimization_level=1, backend=backend)
isa_circuit = pm.run(qc)
isa_operators_list = [op.apply_layout(isa_circuit.layout) for op in operators]

# --- Paso 3: Ejecutar en el hardware ----------------------------------------
options = EstimatorOptions()
options.resilience_level = 1
options.dynamical_decoupling.enable = True
options.dynamical_decoupling.sequence_type = "XY4"

estimator = Estimator(backend, options=options)

job = estimator.run([(isa_circuit, isa_operators_list)])
job_id = job.job_id()
print(f">>> Job ID: {job_id}")
if args.hardware:
    with open(RESULTADOS / "job_ids.txt", "a", encoding="utf-8") as f:
        f.write(f"{datetime.now():%Y-%m-%d %H:%M}  ghz{n}  {backend.name}  {job_id}\n")
    print("Esperando resultado (puede tardar si hay cola). Si cierras la terminal,")
    print(f"recuperalo luego con:  python 04_recuperar_job.py {job_id} --ghz")
else:
    print("Simulando (unos 30 segundos)...")

# --- Paso 4: Post-procesar y graficar ---------------------------------------
data = list(range(1, len(operators) + 1))  # distancia entre qubits
result = job.result()[0]
values = result.data.evs
values = [v / values[0] for v in values]  # normalizar respecto a <Z_1 Z_0>

texto = "\n".join(
    [f"Backend: {backend.name} ({modo})", f"Job ID: {job_id}", f"n = {n}", "", "Distancia   <ZiZ0>/<Z1Z0>"]
    + [f"{d:>9}   {v:.4f}" for d, v in zip(data, values)]
)
print(texto)
(RESULTADOS / f"03_ghz{n}_valores_{modo}.txt").write_text(texto + "\n", encoding="utf-8")

fig = plt.figure()
plt.plot(data, values, marker="o", label=f"{n}-qubit GHZ state")
plt.xlabel("Distance between qubits $i$")
plt.ylabel(r"$\langle Z_i Z_0 \rangle / \langle Z_1 Z_0 \rangle $")
plt.title(f"GHZ {n} qubits - {backend.name} ({modo})")
plt.legend()
ruta = RESULTADOS / f"03_ghz{n}_resultado_{modo}.png"
fig.savefig(ruta, bbox_inches="tight")
print(f"  figura guardada: {ruta}")
plt.show()
