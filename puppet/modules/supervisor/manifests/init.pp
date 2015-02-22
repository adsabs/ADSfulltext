class supervisor($supervisor_conf = 'supervisor.conf'){

 $path_var = "/usr/bin:/usr/sbin:/bin:/usr/local/sbin:/usr/sbin:/sbin"

 exec {'supervisor_install':
    command => 'pip install supervisor',
    path => $path_var,
 }

 file {$supervisor_conf:
    owner => 'vagrant',
    group => 'supervisor',
    mode => '700',
    replace => true,
    source => 'puppet:///modules/supervisor/${supervisor_conf}'
    }
}

class {'supervisor':
    $supervisor_conf => 'supervisor.conf',
}
