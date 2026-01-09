NAME_ARG=""
API_KEY_ARG=""

while [[ $# -gt 0 ]]; do
  case "$1" in 
    --name|-n)
      if [[ -z "$2" ]]; then
        echo "Error: --name requires a value." >&2
        exit 1
      fi
      NAME_ARG="--name $2"
      shift 2
      ;;
    --api-key)
      if [[ -z "$2" ]]; then
        echo "Error: --api-key requires a value." >&2
        exit 1
      fi
      API_KEY_ARG="-e GOOGLE_API_KEY=$2"
      shift 2
      ;;
  esac
done

docker run -it \
  --shm-size 24G \
  -e TZ=Asia/Tokyo \
  -w /workspace \
  -v "$(pwd)":/workspace \
  $NAME_ARG \
  $API_KEY_ARG \
  aobazero_eval \
  /bin/bash