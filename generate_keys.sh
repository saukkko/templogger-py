#!/bin/sh
set -e

force=
quiet=

if [ "$1" = "-f" ] || [ "$2" = "-f" ]; then
    force=1
fi
if [ "$1" = "-q" ] || [ "$2" = "-q" ]; then
    quiet=1
fi

pwdfile=/dev/shm/pwd
key_path="$PWD/keys"
algo="ED448"
cipher="aes256"

priv_key_file="$key_path/private_key.pem"
pub_key_file="$key_path/pubkey.pem"


n1=${#key_path}
n2="$((n1 - ${#algo}))"
n3="$((n1 - ${#cipher}))"

if [ ! $quiet ]; then
    printf "*** Generating NEW private/public keys ***\n"
    printf "+-------------------------"; printf "%${n1}s" | tr " " "-"; printf "+\n"
    printf "| Path................ '%s' |\n" "$key_path"
    printf "| Algorithm........... '%s'" "$algo"; printf "%${n2}s"; printf " |\n"
    printf "| Encryption cipher... '%s'" "$cipher"; printf "%${n3}s"; printf " |\n"
    printf "+-------------------------"; printf "%${#key_path}s" | tr " " "-"; printf "+\n"
fi

REPLY=""
if [ $force ]; then
    REPLY="y"
else
    printf "Your old keys WILL BE DELETED. Continue? [Y/n]: "
    read -r REPLY
fi

cont="n"
case $REPLY in
    "n")
        cont="n"
        ;;
    "N")
        cont="n"
        ;;
    "y")
        cont="y"
        ;;
    "Y")
        cont="y"
        ;;
    *)
        cont="y"
        ;;
esac

if [ ! $quiet ] || [ ! $force ]; then
    printf "\n"

    if [ $cont != "y" ]; then
        printf "exiting\n"
        exit 1
    fi

    printf "\n"
fi

###

###

mkdir -pv "$key_path"
genpw() {
    a=$(od -vAn -N16 -ta < /dev/urandom | sed -e 's/\s//g' -e 's/'\''//g')
    b=$(od -vAn -N16 -ta < /dev/urandom | sed -e 's/\s//g' -e 's/'\''//g')
    printf "%s" "$a$b"
}

printf "%s" "$(genpw)" > $pwdfile

if [ -f "$priv_key_file" ]; then rm -v "$priv_key_file"; fi
if [ -f "$pub_key_file" ]; then rm -v "$pub_key_file"; fi

if [ -f /usr/bin/openssl ]; then
    /usr/bin/openssl genpkey -pass file:$pwdfile -algorithm $algo -$cipher -out "$priv_key_file"
    /bin/chmod -v 600 "$priv_key_file"
    /usr/bin/openssl pkey -passin file:$pwdfile -in "$priv_key_file" -pubout -out "$pub_key_file"
    printf "PRIVATE_KEY_PASSPHRASE='%s'\n" "$(cat $pwdfile)" >> "$key_path/../.env"
    rm -vf $pwdfile
fi

printf "Done\n"
