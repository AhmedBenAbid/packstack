
# Ensure Firewall changes happen before nova services start
# preventing a clash with rules being set by nova-compute and nova-network
Firewall <| |> -> Class['nova']

nova_config{
    "DEFAULT/metadata_host": value => "%(CONFIG_NOVA_API_HOST)s";
}

class {"nova":
    glance_api_servers => "%(CONFIG_GLANCE_HOST)s:9292",
    sql_connection => "mysql://nova:%(CONFIG_NOVA_DB_PW)s@%(CONFIG_MYSQL_HOST)s/nova",
    qpid_hostname => "%(CONFIG_QPID_HOST)s",
    rpc_backend => 'nova.rpc.impl_qpid',
}
