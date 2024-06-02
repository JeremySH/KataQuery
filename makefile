# pick your platform, sorted by typical use
KATAGO_SWITCHES = -DUSE_BACKEND=OPENCL
#KATAGO_SWITCHES = -DUSE_BACKEND=CUDA
#KATAGO_SWITCHES = -DUSE_BACKEND=TENSORRT
#KATAGO_SWITCHES = -DUSE_BACKEND=EIGEN -DUSE_AVX2=1 # if you can use it
#KATAGO_SWITCHES = -DUSE_BACKEND=EIGEN

CYTHONIZE_IT ?=0 # 1 to Cythonize
CYTHONIC = 

PY_SOURCES = \
BoardController.py \
GameSettingsDialog.py \
GameSettingsDialog_ui.py \
GlobalSignals.py \
NeuralNetSettingsDialog_ui.py \
SgfParser.py \
codeeditor.py \
goban.py \
goutils.py \
kataproxy.py \
main.py \
mainwindow_ui.py \
project_globals.py \

UI_FILES = \
GameSettingsDialog.ui \
NeuralNetSettingsDialog.ui \
mainwindow.ui

ifneq ($(strip $(CYTHONIZE_IT)),0)
	CYTHONIC = build_receipts/cythonized_built
endif

# i have to use build receipts for now because
# these tools create random filenames per architecture
# but success of build can always be confirmed

.PHONY: all
all: build_receipts/command-line_built build_receipts/app_built

app: build_receipts/app_built

command-line: build_receipts/command-line_built

build_receipts/command-line_built: build_receipts/receipts_ready build_receipts/venv_built build_receipts/ui_built katago-bin/katago $(CYTHONIC) 
	touch build_receipts/command-line_built


KataGo/cpp/katago:
	# cmake scatters files everywhere but build isn't easy out-of-source
	# so don't worry & be happy
	cd KataGo/cpp && cmake . $(KATAGO_SWITCHES) && make -j

katago-bin/katago: KataGo/cpp/katago
	mkdir -p katago-bin
	/bin/cp -f KataGo/cpp/katago katago-bin/

build_receipts/receipts_ready: 
	mkdir -p build_receipts
	touch build_receipts/receipts_ready

build_receipts/venv_built: build_receipts/receipts_ready
	sh -c "python3.9 -m venv venv && . venv/bin/activate && pip install \
	pyqt5==5.15.10 \
	pandas==2.2.2 \
	matplotlib==3.9.0 \
	pyqode-core==4.0.11 \
	pyqode.qt==2.10.0 \
	pyqode.python==4.0.2 \
	Pygments==2.17.2 \
	pillow==10.3.0 \
	pyinstaller==6.6.0 \
	&& deactivate && touch build_receipts/venv_built" 

build_receipts/ui_built: build_receipts/venv_built $(UI_FILES) 
	. venv/bin/activate && pyuic5 -o mainwindow_ui.py mainwindow.ui ; deactivate
	. venv/bin/activate && pyuic5 -o GameSettingsDialog_ui.py GameSettingsDialog.ui ; deactivate
	. venv/bin/activate && pyuic5 -o NeuralNetSettingsDialog_ui.py NeuralNetSettingsDialog.ui ; deactivate
	touch build_receipts/ui_built

# cython is a bit of added complexity for small benefit
# so for the moment allow building for testing
# but don't actually use unless manually invoked
.PHONY: cythonized
cythonized: build_receipts/cythonized_built

build_receipts/cythonized_built: $(PY_SOURCES) build_receipts/receipts_ready
	. venv/bin/activate && cythonize -b -3 -X annotation_typing=True BoardController.py && deactivate && rm BoardController.c
	. venv/bin/activate && cythonize -b -3 -X annotation_typing=True goban.py && deactivate && rm goban.c
	. venv/bin/activate && cythonize -b -3 -X annotation_typing=True kataproxy.py && deactivate && rm kataproxy.c
	touch build_receipts/cythonized_built

build_receipts/app_built: $(PY_SOURCES) $(CYTHONIC) main.spec build_receipts/venv_built build_receipts/ui_built katago-bin/katago
	. venv/bin/activate && pyinstaller --noconfirm main.spec && deactivate
	touch build_receipts/app_built

.PHONY: clean
clean:
	rm -rf build_receipts
	cd KataGo/cpp && make clean
	rm -f katago-bin/katago
	rm -rf venv
	rm -f GameSettingsDialog_ui.py NeuralNetSettingsDialog_ui.py mainwindow_ui.py
	rm -rf build
	rm -rf dist
	rm *.so

