# Laboratorio: Hello world en IBM Quantum

Implementación del tutorial oficial
[Hello world / Run your first circuit on hardware](https://quantum.cloud.ibm.com/docs/en/ibm-quantum-compute/hello-world)
con Qiskit 2.6.2 y qiskit-ibm-runtime 0.52.1 (ya instalados en `.venv`).

## Archivos

| Archivo | Qué hace | ¿Necesita API key? |
|---|---|---|
| `00_verificar_instalacion.py` | Bell + histograma con simulador ideal (verifica la instalación) | No |
| `01_guardar_cuenta.py` | Guarda tu API key de IBM (una sola vez) y prueba la conexión | **Sí, te la pide** |
| `02_bell_state.py` | **Parte 1** del tutorial: estado de Bell + 6 observables con el Estimator | Solo con `--hardware` |
| `03_ghz_100_qubits.py` | **Parte 2** del tutorial: estado GHZ de 100 qubits | Solo con `--hardware` |
| `04_recuperar_job.py` | Recupera el resultado de un job por su ID (si cerraste la terminal) | Sí |
| `hello_world.ipynb` | Todo el tutorial en notebook (variable `USAR_HARDWARE`) | Solo si `USAR_HARDWARE = True` |
| `resultados/` | Gráficas `.png`, valores `.txt` y `job_ids.txt` | — |

## Cómo ejecutar (PowerShell, dentro de esta carpeta)

Usa siempre el Python del entorno virtual `.venv`:

```powershell
.\.venv\Scripts\python.exe 00_verificar_instalacion.py
```

### 1. Probar en simulador (sin cuenta)

```powershell
.\.venv\Scripts\python.exe 02_bell_state.py
```

```powershell
.\.venv\Scripts\python.exe 03_ghz_100_qubits.py
```

El modo simulador usa backends "fake" con el ruido de equipos IBM reales
(`FakeBelemV2` para Bell y `FakeGuadalupeV2` con n = 10 para GHZ, porque 100 qubits no se pueden simular en una PC).

### 2. Guardar la API key (una sola vez)

1. Entra a https://quantum.cloud.ibm.com e inicia sesión (plan **Open** = gratis, 10 min de QPU al mes).
2. En el dashboard crea tu **API key** (44 caracteres) y cópiala.
3. (Opcional) En **Instances** copia el **CRN** de tu instancia.
4. Ejecuta y pega la clave cuando te la pida (no se ve al escribir):

```powershell
.\.venv\Scripts\python.exe 01_guardar_cuenta.py
```

La clave queda en `%USERPROFILE%\.qiskit\qiskit-ibm.json`, fuera del proyecto.

### 3. Ejecutar en una computadora cuántica real

```powershell
.\.venv\Scripts\python.exe 02_bell_state.py --hardware
```

```powershell
.\.venv\Scripts\python.exe 03_ghz_100_qubits.py --hardware
```

Cada job imprime su **Job ID** y lo anota en `resultados/job_ids.txt`. Si la cola es larga y cierras la terminal:

```powershell
.\.venv\Scripts\python.exe 04_recuperar_job.py <JOB_ID>
```

(agrega `--ghz` si el job es del script 03). También puedes ver tus jobs en https://quantum.cloud.ibm.com/workloads.

### Notebook

```powershell
.\.venv\Scripts\python.exe -m notebook hello_world.ipynb
```

En VS Code: abre `hello_world.ipynb` y elige el kernel/intérprete `.venv`.
Cambia `USAR_HARDWARE = True` en la segunda celda para usar hardware real.

## Resultados esperados

- **Bell:** ⟨ZZ⟩ ≈ 1 y ⟨XX⟩ ≈ 1; ⟨IZ⟩, ⟨IX⟩, ⟨ZI⟩, ⟨XI⟩ ≈ 0 (qubits entrelazados).
- **GHZ:** ⟨Z₀Zᵢ⟩/⟨Z₀Z₁⟩ empieza en 1 y decae con la distancia por el ruido (lo ideal sería 1 en todos).

## Si reinstalas

```powershell
py -3.12 -m venv .venv
```

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```
