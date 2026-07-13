#!/bin/bash
# Ignis — Setup .bashrc pour le banc de simulation
export HOME=/home/camil

# Copier premier_vol.py
cp /mnt/a/GSIE/22_PROJECT_MEMORY/Ignis/premier_vol.py ~/Ignis/scripts/premier_vol.py
echo "Script premier_vol.py copie"

# Ajouter PATH forefire au .bashrc si absent
if ! grep -q 'Ignis/forefire/build/bin' ~/.bashrc; then
    echo 'export PATH=$PATH:~/Ignis/forefire/build/bin' >> ~/.bashrc
    echo "PATH forefire ajoute au .bashrc"
else
    echo "PATH forefire deja present"
fi

# Ajouter activation venv au .bashrc si absent
if ! grep -q 'Ignis/.venv/bin/activate' ~/.bashrc; then
    echo 'source ~/Ignis/.venv/bin/activate' >> ~/.bashrc
    echo "Activation venv ajoutee au .bashrc"
else
    echo "Activation venv deja presente"
fi

echo "=== .bashrc (dernieres lignes) ==="
tail -5 ~/.bashrc
