
class {"mysql::server":
    config_hash => {bind_address => "0.0.0.0",
                    root_password => "%(CONFIG_MYSQL_PW)s",}
}

# deleting database users for security
# this is done in mysql::server::account_security but has problems
# when there is no fqdn, so we're defining a slightly different one here
database_user { [ 'root@127.0.0.1', 'root@::1', '@localhost', '@%%' ]:
    ensure  => 'absent', require => Class['mysql::config'],
}
if ($::fqdn != "" and $::fqdn != "localhost") {
    database_user { [ "root@${::fqdn}", "@${::fqdn}"]:
        ensure  => 'absent', require => Class['mysql::config'],
    }
}
if ($::fqdn != $::hostname and $::hostname != "localhost") {
    database_user { ["root@${::hostname}", "@${::hostname}"]:
        ensure  => 'absent', require => Class['mysql::config'],
    }
}


class {"keystone::db::mysql":
    password      => "%(CONFIG_KEYSTONE_DB_PW)s",
    allowed_hosts => "%%",
}


firewall { '001 mysql incoming':
    proto    => 'tcp',
    dport    => ['3306'],
    action   => 'accept',
}
