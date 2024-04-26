all: katago-bin/katago venv mainwindow_ui.py GameSettingsDialog_ui.py

katago: katago-bin/katago

venv:
	sh -c "python3.9 -m venv venv && . venv/bin/activate && pip install \
	pyqt5==5.15.10 \
	pandas==2.2.2 \
	pyqode-core==4.0.11 \
	pyqode.qt==2.10.0 \
	pyqode.python==4.0.2 \
	Pygments==2.17.2 \
	&& deactivate" 

katago-bin/katago: KataGo/cpp/katago
	mkdir -p katago-bin
	/bin/cp -f KataGo/cpp/katago katago-bin/

KataGo/cpp/katago:
	# cmake scatters files everywhere but build isn't easy out-of-source
	# so don't worry & be happy
	cd KataGo/cpp && cmake . -DUSE_BACKEND=OPENCL && make -j

mainwindow_ui.py: venv mainwindow.ui
	. venv/bin/activate && pyuic5 -o mainwindow_ui.py mainwindow.ui ; deactivate

GameSettingsDialog_ui.py: venv GameSettingsDialog.ui
	. venv/bin/activate && pyuic5 -o GameSettingsDialog_ui.py GameSettingsDialog.ui ; deactivate

clean:
	cd KataGo/cpp && make clean
	rm -f katago-bin/katago
	rm -rf venv

