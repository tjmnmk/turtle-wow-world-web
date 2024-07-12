<?php

# connect to redis
$redis = new Redis();
$redis->connect('localhost', 6379);

# redis_get_max_id
$max_id = $redis->get('max_id');
$max_id = intval($max_id);

# get id from get argument
$client_message_id = $_GET['message_id'];

# die if not client_message_id or not numeric
if (!isset($client_message_id)) {
    die();
}
if (!is_numeric($client_message_id)) {
    die();
}

$client_message_id = intval($client_message_id);

if ($client_message_id < ($max_id - 250)) {
    $client_message_id = $max_id - 250;
}

# redis get messages
$messages = [];
for ($id = $client_message_id + 1; $id <= $max_id; $id++) {
    $messages[] = $redis->get('' . $id);
}

# implode messages with br
$messages = implode('<br>', $messages);
# add br to the end of messages if not empty
if ($messages !== '') {
    $messages .= '<br>';
}

# create json with max_id and messages as html by br
echo json_encode(['client_message_id' => $max_id, 
                  'messages' => $messages]);


