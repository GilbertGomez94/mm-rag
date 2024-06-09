# Bienvenidos al mundo del RAG Multimodal

Antes que nada, hablemos de lo que necesitan instalar previo al inicio del taller.

- Instalar [Python](https://phoenixnap.com/kb/how-to-install-python-3-ubuntu) >= 3.10 (no se ha probado en versiones inferiores)
- Instalar [Visual Studio Code](https://code.visualstudio.com/download)(o el editor que código para Python que más te guste)
- Instalar [Poppler](https://pdf2image.readthedocs.io/en/latest/installation.html) -> Solo si ejecutan el notebook en local(no recomendado en el taller)
- Instalar [Tesseract](https://tesseract-ocr.github.io/tessdoc/Installation.html) -> Solo si ejecutan el notebook en local(no recomendado en local)
- (Opcional) Instalar Make en su OS (Lo pueden no instalar y simplemente ir al Makefile e ir ejecutando los comandos uno a uno, simplemente es para facilitar la ejecución de comandos) [MacOS](https://formulae.brew.sh/formula/make) [Ubuntu](https://www.drupaladicto.com/snippet/como-instalar-make-en-ubuntu) 
- Ejecutar el comando `make install` que se encuentra dentro del Makefile. En caso de que prefieran trabajar con Anaconda para las versiones de python, deben usar el comando `make condainstall`. Pueden usar [pyenv](https://github.com/pyenv/pyenv?tab=readme-ov-file#installation), sin embargo no lo he usado tanto, queda a discreción de cada quién, no dejo un Make para esta librería.


# Link al Notebook:
https://drive.google.com/file/d/1M_7eZQ8dCUyAlJPIDv5Zbtjl49u8Pv11/view?usp=sharing

# En caso de errores:

En caso de tener el siguiente error `ERROR: Could not build wheels for pycocotools, which is required to install pyproject.toml-based projects`
Deben instalar en su OS, dependiendo de la versión de python que tengan allí las instalaciones dev de python, es decir, el siguiente comando:
- Ubunut: sudo apt install gcc
- Macos: brew install gcc

En caso de que esto falle, pueden intentar con la instalación de las dependencias de desarrollo de python:

- Ubuntu: sudo apt install python3.x-dev
- MacOS: No veo ningún comando.

