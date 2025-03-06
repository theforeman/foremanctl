<configuration xmlns="urn:activemq"
               xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
               xsi:schemaLocation="urn:activemq /schema/artemis-configuration.xsd">

    <core xmlns="urn:activemq:core" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
          xsi:schemaLocation="urn:activemq:core ">

	<!-- Disable 'hot reloading' this broker.xml file; we are not making changes at runtime -->
        <configuration-file-refresh-period>-1</configuration-file-refresh-period>

        <acceptors>
            <acceptor name="in-vm">vm://0</acceptor>
            <acceptor name="stomp">tcp://localhost:61613?protocols=STOMP;useEpoll=false;sslEnabled=true;trustStorePath=${CANDLEPIN_TRUSTSTORE_PATH};trustStorePassword=${CANDLEPIN_TRUSTSTORE_PASSWORD};keyStorePath=${CANDLEPIN_KEYSTORE_PATH};keyStorePassword=${CANDLEPIN_KEYSTORE_PASSWORD};needClientAuth=true</acceptor>
        </acceptors>

        <security-enabled>true</security-enabled>

        <security-settings>
            <security-setting match="katello.candlepin.#">
                <permission type="consume" roles="candlepinEventsConsumer"/>
            </security-setting>
            <security-setting match="#">
                <permission type="createAddress" roles="invm-role"/>
                <permission type="deleteAddress" roles="invm-role"/>
                <permission type="createDurableQueue" roles="invm-role"/>
                <permission type="deleteDurableQueue" roles="invm-role"/>
                <permission type="createNonDurableQueue" roles="invm-role"/>
                <permission type="deleteNonDurableQueue" roles="invm-role"/>
                <permission type="send" roles="invm-role"/>
                <permission type="consume" roles="invm-role"/>
                <permission type="browse" roles="invm-role"/>
                <permission type="manage" roles="invm-role"/>
            </security-setting>
        </security-settings>

        <!-- Silence warnings on server startup -->
        <cluster-user></cluster-user>
        <cluster-password></cluster-password>

        <persistence-enabled>true</persistence-enabled>
        <journal-type>NIO</journal-type>
        <journal-pool-files>1</journal-pool-files>
        <create-bindings-dir>true</create-bindings-dir>
        <create-journal-dir>true</create-journal-dir>
        <bindings-directory>/var/lib/candlepin/activemq-artemis/bindings</bindings-directory>
        <journal-directory>/var/lib/candlepin/activemq-artemis/journal</journal-directory>
        <large-messages-directory>/var/lib/candlepin/activemq-artemis/largemsgs</large-messages-directory>
        <paging-directory>/var/lib/candlepin/activemq-artemis/paging</paging-directory>

        <!-- Only block message delivery once the disk is 99% used (1% remaining) -->
        <max-disk-usage>99</max-disk-usage>

        <addresses>
            <address name="event.default">
                <multicast>
                    <queue name="event.org.candlepin.audit.LoggingListener" />
                    <queue name="event.org.candlepin.audit.ActivationListener" />
                </multicast>
            </address>

            <address name="katello.candlepin">
                <multicast>
                  <queue name="katello_candlepin_event_monitor.candlepin_events" max-consumers="1" />
                </multicast>
            </address>

            <address name="job">
                <anycast>
                    <queue name="jobs"/>
                </anycast>
            </address>
        </addresses>

        <address-settings>
            <address-setting match="event.default">
                <config-delete-queues>FORCE</config-delete-queues>
                <auto-create-queues>true</auto-create-queues>
                <max-size-bytes>10485760</max-size-bytes>

                <!-- By default, Artemis will page messages when the queue address is full. -->
                <page-size-bytes>1048576</page-size-bytes>

                <!--
                    Configure message redelivery. We set the maximum number of times that a message should
                    be redelivered to 0 so that messages will remain in the queue and will never get sent
                    to the dead letter queue. Since candlepin does not currently set up, or use, a dead
                    letter queue, any messages sent there will be lost. We need to prevent this.
                -->
                <redelivery-delay>30000</redelivery-delay>
                <max-redelivery-delay>3600000</max-redelivery-delay>
                <redelivery-delay-multiplier>2</redelivery-delay-multiplier>
                <max-delivery-attempts>0</max-delivery-attempts>
            </address-setting>

            <address-setting match="katello.candlepin">
                <auto-create-queues>false</auto-create-queues>
                <max-size-bytes>10485760</max-size-bytes>

                <!-- By default, Artemis will page messages when the queue address is full. -->
                <page-size-bytes>1048576</page-size-bytes>

                <redelivery-delay>0</redelivery-delay>
                <max-delivery-attempts>1</max-delivery-attempts>
            </address-setting>

            <address-setting match="job">
                <max-size-bytes>10485760</max-size-bytes>

                <!-- By default, Artemis will page messages when the queue address is full. -->
                <page-size-bytes>1048576</page-size-bytes>

                <!--
                    Default the consumer window size to zero so we don't have a single thread grabbing
                    a ton of job messages and choking out other threads that are waiting for work.
                -->
                <default-consumer-window-size>0</default-consumer-window-size>

                <!-- Redelivery config -->
                <redelivery-delay>30000</redelivery-delay>
                <max-redelivery-delay>3600000</max-redelivery-delay>
                <redelivery-delay-multiplier>2</redelivery-delay-multiplier>
                <max-delivery-attempts>0</max-delivery-attempts>
            </address-setting>
        </address-settings>

        <diverts>
            <divert name="katello_divert">
                <exclusive>false</exclusive>
                <address>event.default</address>
                <filter string="
                    (EVENT_TARGET='COMPLIANCE' and EVENT_TYPE='CREATED') OR
                    (EVENT_TARGET='SYSTEM_PURPOSE_COMPLIANCE' and EVENT_TYPE='CREATED') OR
                    (EVENT_TARGET='POOL' and EVENT_TYPE='CREATED') OR
                    (EVENT_TARGET='POOL' and EVENT_TYPE='DELETED') OR
                    (EVENT_TARGET='ENTITLEMENT' and EVENT_TYPE='CREATED') OR
                    (EVENT_TARGET='ENTITLEMENT' and EVENT_TYPE='DELETED') OR
                    (EVENT_TARGET='OWNER_CONTENT_ACCESS_MODE' and EVENT_TYPE='MODIFIED')
                "/>
                <forwarding-address>katello.candlepin</forwarding-address>
            </divert>
        </diverts>
    </core>
</configuration>
