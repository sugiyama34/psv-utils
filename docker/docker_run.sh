NAME_ARG=""
PORT_ARG=""

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
    --port|-p)
      if [[ -z "$2" ]]; then
        echo "Error: --port requires a value." >&2
        exit 1
      fi
      PORT_ARG="-p $2:$2"
      shift 2
      ;;
    *)
      echo "Error: unknown option: $1" >&2
      exit 1
      ;;
  esac
done

echo "NAME_ARG: $NAME_ARG"
echo "PORT_ARG: $PORT_ARG"

docker run -it \
  --shm-size 24G \
  -e TZ=Asia/Tokyo \
  -w /workspace \
  -v "$(pwd)":/workspace \
  $NAME_ARG \
  $PORT_ARG \
  aobazero_eval \
  /bin/bash