"""Problema propuesto - Algoritmo de Bernstein-Vazirani.

Una "caja negra" (oraculo) esconde un numero secreto s de n bits. Al darle un
numero x responde un solo bit: f(x) = s . x (mod 2), la paridad de los bits de
x que coinciden con los 1 de s.

  - Clasicamente se necesitan n consultas (una por bit: 1000, 0100, 0010, 0001).
  - Con un computador cuantico basta UNA consulta: se mide s directamente.

Uso:
    python 05_bernstein_vazirani.py                       -> simulador con ruido (FakeGuadalupeV2), secreto 1011
    python 05_bernstein_vazirani.py --hardware            -> QPU real de IBM
    python 05_bernstein_vazirani.py --secreto 110101      -> elegir otro secreto (solo 0 y 1)
"""

import argparse
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
from qiskit import QuantumCircuit
from qiskit.transpiler import generate_preset_pass_manager
from qiskit.visualization import plot_histogram
from qiskit_ibm_runtime.executor_sampler import Sampler

parser = argparse.ArgumentParser(description="Algoritmo de Bernstein-Vazirani")
parser.add_argument("--hardware", action="store_true", help="ejecutar en una QPU real de IBM")
parser.add_argument("--secreto", default="1011", help="numero secreto en binario (por defecto 1011)")
parser.add_argument("--shots", type=int, default=4000, help="numero de repeticiones (por defecto 4000)")
args = parser.parse_args()
secreto = args.secreto
if not secreto or set(secreto) - {"0", "1"}:
    raise SystemExit("El secreto debe estar formado solo por 0 y 1, por ejemplo 1011")
n = len(secreto)
modo = "hardware" if args.hardware else "simulador"

RESULTADOS = Path(__file__).parent / "resultados"
RESULTADOS.mkdir(exist_ok=True)


def guardar(fig, nombre):
    ruta = RESULTADOS / nombre
    fig.savefig(ruta, bbox_inches="tight")
    plt.close(fig)
    print(f"  figura guardada: {ruta}")


# --- Version clasica (para comparar) ----------------------------------------
def oraculo_clasico(x: str) -> int:
    """f(x) = s . x mod 2"""
    return sum(int(a) * int(b) for a, b in zip(secreto, x)) % 2


consultas = 0
bits = ""
for i in range(n):
    x = "0" * i + "1" + "0" * (n - i - 1)   # 1000, 0100, 0010, ...
    bits += str(oraculo_clasico(x))
    consultas += 1
print(f"Clasico: secreto encontrado = {bits} usando {consultas} consultas al oraculo")


# --- Paso 1: Mapear el problema a un circuito cuantico ------------------------
def oraculo_cuantico(qc: QuantumCircuit, s: str) -> None:
    """CNOT desde cada qubit donde el secreto tiene un 1 hacia el qubit auxiliar.
    Qiskit numera los bits de derecha a izquierda: el qubit 0 es el ultimo caracter de s."""
    aux = len(s)
    for i, bit in enumerate(reversed(s)):
        if bit == "1":
            qc.cx(i, aux)


def circuito_bernstein_vazirani(s: str) -> QuantumCircuit:
    n = len(s)
    qc = QuantumCircuit(n + 1, n)
    qc.x(n)                 # qubit auxiliar en |1>
    qc.h(range(n + 1))      # entradas en superposicion y auxiliar en |->
    qc.barrier()
    oraculo_cuantico(qc, s)  # UNA sola consulta al oraculo
    qc.barrier()
    qc.h(range(n))          # interferencia: deja el secreto en las entradas
    qc.measure(range(n), range(n))
    return qc


qc = circuito_bernstein_vazirani(secreto)
print(qc.draw("text"))
guardar(qc.draw("mpl"), f"05_bv_circuito_{secreto}.png")

# --- Paso 2: Optimizar para el hardware -------------------------------------
if args.hardware:
    from qiskit_ibm_runtime import QiskitRuntimeService

    service = QiskitRuntimeService()
    backend = service.least_busy(simulator=False, operational=True, min_num_qubits=n + 1)
else:
    from qiskit_ibm_runtime.fake_provider import FakeGuadalupeV2

    backend = FakeGuadalupeV2()
    if n + 1 > backend.num_qubits:
        raise SystemExit(f"El simulador tiene {backend.num_qubits} qubits; usa un secreto de hasta {backend.num_qubits - 1} bits")
print(f"Backend ({modo}): {backend.name}")

pm = generate_preset_pass_manager(backend=backend, optimization_level=1)
isa_circuit = pm.run(qc)
print(f"Circuito transpilado: profundidad {isa_circuit.depth()}, "
      f"compuertas de 2 qubits: {isa_circuit.num_nonlocal_gates()}")
guardar(isa_circuit.draw("mpl", idle_wires=False, fold=-1), f"05_bv_circuito_isa_{modo}.png")

# --- Paso 3: Ejecutar con el Sampler ----------------------------------------
sampler = Sampler(mode=backend)
sampler.options.default_shots = args.shots

job = sampler.run([isa_circuit])
job_id = job.job_id()
print(f">>> Job ID: {job_id}")
if args.hardware:
    with open(RESULTADOS / "job_ids.txt", "a", encoding="utf-8") as f:
        f.write(f"{datetime.now():%Y-%m-%d %H:%M}  bv{secreto}  {backend.name}  {job_id}\n")
    print("Esperando resultado (puede tardar si hay cola)...")

# --- Paso 4: Post-procesar ---------------------------------------------------
counts = job.result()[0].data.c.get_counts()
total = sum(counts.values())
ganador = max(counts, key=counts.get)
prob_secreto = counts.get(secreto, 0) / total

top = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)[:5]
lineas = [
    f"Backend: {backend.name} ({modo})",
    f"Job ID: {job_id}",
    f"Secreto: {secreto}  (n = {n} bits, {n + 1} qubits)",
    f"Shots: {total}",
    f"Resultado mas frecuente: {ganador}  -> {'CORRECTO' if ganador == secreto else 'INCORRECTO'}",
    f"Probabilidad de medir el secreto: {prob_secreto:.4f}",
    f"Consultas al oraculo: cuantico = 1, clasico = {n}",
    "",
    "Top 5 resultados (bits: conteo):",
] + [f"  {b}: {c}" for b, c in top]
texto = "\n".join(lineas)
print(texto)
(RESULTADOS / f"05_bv_{secreto}_valores_{modo}.txt").write_text(texto + "\n", encoding="utf-8")

fig = plot_histogram(counts, sort="value_desc", number_to_keep=8,
                     title=f"Bernstein-Vazirani, secreto {secreto} - {backend.name} ({modo})")
fig.savefig(RESULTADOS / f"05_bv_{secreto}_histograma_{modo}.png", bbox_inches="tight")
print(f"  figura guardada: {RESULTADOS / f'05_bv_{secreto}_histograma_{modo}.png'}")
plt.show()
