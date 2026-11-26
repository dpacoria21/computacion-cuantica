"""Paso 0 - Verifica la instalacion de Qiskit (no necesita cuenta de IBM).

Construye un estado de Bell, lo mide 1024 veces con un simulador ideal y
muestra el histograma. Se espera ~50% '00' y ~50% '11'.

Uso:
    python 00_verificar_instalacion.py
"""

from pathlib import Path

import matplotlib.pyplot as plt
import qiskit
import qiskit_ibm_runtime
from qiskit import QuantumCircuit
from qiskit.primitives import StatevectorSampler
from qiskit.visualization import plot_histogram

RESULTADOS = Path(__file__).parent / "resultados"
RESULTADOS.mkdir(exist_ok=True)

print(f"qiskit {qiskit.__version__} | qiskit-ibm-runtime {qiskit_ibm_runtime.__version__}")

qc = QuantumCircuit(2)
qc.h(0)
qc.cx(0, 1)
qc.measure_all()
print(qc.draw("text"))

sampler = StatevectorSampler()
result = sampler.run([qc], shots=1024).result()
counts = result[0].data.meas.get_counts()
print("Conteos:", counts)

fig = plot_histogram(counts, title="Estado de Bell (simulador ideal)")
ruta = RESULTADOS / "00_histograma_bell.png"
fig.savefig(ruta, bbox_inches="tight")
print(f"Histograma guardado en {ruta}")
plt.show()
