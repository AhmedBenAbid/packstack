
# Ensure Firewall changes happen before nova services start
# preventing a clash with rules being set by nova-compute and nova-network
Firewall <| |> -> Class['nova']

nova_config{
    "metadata_host": value => "%(CONFIG_NOVA_API_HOST)s";
    "qpid_hostname": value => "%(CONFIG_QPID_HOST)s";
    "rpc_backend": value => "nova.rpc.impl_qpid";
}

class {"nova":
    glance_api_servers => "%(CONFIG_GLANCE_HOST)s:9292",
    sql_connection => "mysql://nova:%(CONFIG_NOVA_DB_PW)s@%(CONFIG_MYSQL_HOST)s/nova",
}
