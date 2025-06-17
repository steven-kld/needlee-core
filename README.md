# core.tete-a-tete

✅ Minimum server requirements
OS: Ubuntu 22.04 LTS
Python: 3.10+ (comes preinstalled)
RAM: 8 GB (enough for small model, borderline for medium)
Disk: 20 GB (room for models + logs)
CPU: Any modern 4-core CPU will work (no AVX needed)


python3 -m pip install --upgrade pip
pip3 install faster-whisper

apt update
apt install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | \
  tee /etc/apt/sources.list.d/docker.list > /dev/null

apt update
apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

/root/echo-core/.env -> env