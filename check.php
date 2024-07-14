<?php

# connect to redis
$redis = new Redis();
$redis->connect('localhost', 6379);

# redis_get_max_id
$max_id = $redis->get('max_id');
$max_id = intval($max_id);

# redis get message with max id
$message = $redis->get('' . $max_id);

# if message print error and return 500
if ($message === false) {
    http_response_code(500);
    echo 'error';
    die();
}

echo "ok";
