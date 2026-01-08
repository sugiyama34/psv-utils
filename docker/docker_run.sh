docker run -it \
  --shm-size 24G \
  -e TZ=Asia/Tokyo \
  -w /workspace \
  aobazero_eval \
  /bin/bash