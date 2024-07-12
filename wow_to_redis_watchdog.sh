#! /bin/bash -u

# get max_id key from redis
max_id=$(redis-cli get max_id)


# get message by max_id
message=$(redis-cli keys "$max_id")


if echo "$message" |grep -q "(empty list or set)"; then
    systemctl restart wow-to-redis
fi

