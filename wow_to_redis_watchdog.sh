#! /bin/bash -u

MIN_TTL=6300 # 7200 - 15 * 60

# get max_id key from redis
max_id=$(redis-cli get max_id)

# get message by max_id
ttl=$(redis-cli ttl "$max_id" |awk '{print $1}')
if [ ! -z "$ttl" ] && [ "$ttl" -gt "$MIN_TTL" ]; then
    exit 0
fi

systemctl restart tclib_to_redis

