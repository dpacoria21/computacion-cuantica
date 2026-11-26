"""Paso 1 - Guarda tu API key de IBM Quantum en este equipo (solo una vez).

La clave se guarda en ~/.qiskit/qiskit-ibm.json (fuera de esta carpeta), asi
que no queda dentro del proyecto. Despues de esto, los demas scripts se
conectan solos con QiskitRuntimeService().

Donde conseguir los datos (https://quantum.cloud.ibm.com):
  - API key: en el dashboard, seccion "API key" -> Create. Tiene 44 caracteres.
  - CRN (opcional): en la pagina "Instances", copia el CRN de tu instancia
    (plan Open = gratis). Si lo dejas vacio, Qiskit usa las instancias de tu cuenta.

Uso:
    python 01_guardar_cuenta.py
"""

import os
import sys
from getpass import getpass

from qiskit_ibm_runtime import QiskitRuntimeService

token = os.environ.get("IBM_QUANTUM_TOKEN") or getpass(
    "Pega tu API key de IBM Quantum (no se vera al escribir) y presiona Enter: "
)
token = token.strip()
if not token:
    sys.exit("No se ingreso ninguna API key.")
if len(token) != 44:
    print(f"Aviso: la API key tiene {len(token)} caracteres (normalmente son 44). Revisa que este completa.")

crn = os.environ.get("IBM_QUANTUM_CRN") or input(
    "CRN de tu instancia (opcional, Enter para omitir): "
)
crn = crn.strip() or None

QiskitRuntimeService.save_account(
    token=token,
    instance=crn,
    overwrite=True,
    set_as_default=True,
)
print("Cuenta guardada en ~/.qiskit/qiskit-ibm.json")

print("Probando la conexion...")
try:
    service = QiskitRuntimeService()
    backends = service.backends(simulator=False, operational=True)
except Exception as exc:  # noqa: BLE001
    sys.exit(f"No se pudo conectar: {exc}\nRevisa la API key / CRN y vuelve a ejecutar este script.")

print(f"Conexion OK. Computadoras cuanticas disponibles ({len(backends)}):")
for b in sorted(backends, key=lambda b: b.status().pending_jobs):
    print(f"  - {b.name:<16} {b.num_qubits:>4} qubits | jobs en cola: {b.status().pending_jobs}")
