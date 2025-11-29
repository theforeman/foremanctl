set -e
file=/opt/kafka/config/kraft/server.properties
bin/kafka-storage.sh format --ignore-formatted -t random-uuid -c $file
exec bin/kafka-server-start.sh $file
