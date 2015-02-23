class supervisor($supervisor_conf = '/etc/supervisor.conf', $upstart_conf = '/etc/init/supervisor.conf'){

  $path_var = '/usr/bin:/usr/sbin:/bin:/usr/local/sbin:/usr/sbin:/sbin'

  exec {'supervisor_install':
    command => 'pip install supervisor',
    path => $path_var,
  }

   file {$supervisor_conf:
     owner => 'vagrant',
     group => 'vagrant',
     mode => '700',
     replace => true,
     source => 'puppet:///modules/supervisor/supervisord.conf',
   }

   file {$upstart_conf:
     owner => 'vagrant',
     group => 'vagrant',
     mode => '700',
     replace => true,
     source => 'puppet:///modules/supervisor/supervisor.conf',
}

class {'supervisor':
    supervisor_conf => '/etc/supervisord.conf',
    upstart_conf => '/etc/init/supervisor.conf',
}
