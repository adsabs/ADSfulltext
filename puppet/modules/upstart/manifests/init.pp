class upstart($supervisor_conf = '/etc/supervisor.conf', $rabbitmq_conf = '/etc/init/rabbitmq.conf'){

   file {$supervisor_conf:
     owner => 'vagrant',
     group => 'vagrant',
     mode => '700',
     replace => true,
     source => 'puppet:///modules/upstart/supervisor.conf',
   }

   file {$rabbitmq_conf:
     owner => 'vagrant',
     group => 'vagrant',
     mode => '700',
     replace => true,
     source => 'puppet:///modules/upstart/rabbitmq.conf',
   }

}

class {'upstart':
    supervisor_conf => '/etc/init/supervisord.conf',
    rabbitmq_conf => '/etc/init/rabbitmq.conf',
}
