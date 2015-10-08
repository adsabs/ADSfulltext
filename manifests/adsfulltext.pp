# Some const. variables
$path_var = "/usr/bin:/usr/sbin:/bin:/usr/local/sbin:/usr/sbin:/sbin"
$build_packages = ['python', 'python-pip', 'python-dev', 'libpq-dev', 'libxml2-dev', 'libxslt1-dev', 'sshfs', 'oracle-java8-installer', 'maven']
$pip_requirements = "/vagrant/requirements.txt"

exec {'add_repo_1':
    command => 'echo "oracle-java8-installer shared/accepted-oracle-license-v1-1 select true" | debconf-set-selections && add-apt-repository ppa:webupd8team/java',
    path => $path_var,
}

# Update package list
exec {'apt_update_1':
	command => 'apt-get update && touch /etc/.apt-updated-by-puppet1',
	creates => '/etc/.apt-updated-by-puppet1',
	path => $path_var,
}

# Install packages
package {$build_packages:
	ensure => installed,
	require => Exec['apt_update_1'],
}

# Install all python dependencies for selenium and general software
exec {'pip_install_modules':
	command => "pip install -r ${pip_requirements}",
	logoutput => on_failure,
	path => $path_var,
	tries => 2,
	timeout => 1000, # This is only require for Scipy/Matplotlib - they take a while
	require => Package[$build_packages],
}

# Python path to work while on the VM
exec {'update_python_path':
    command => "echo 'export PYTHONPATH=$PYTHONPATH:/vagrant/' > /home/vagrant/.bashrc",
    path => $path_var,
}

Exec['add_repo_1'] -> Exec['apt_update_1'] -> Package[$build_packages] -> Exec['pip_install_modules'] -> Exec['update_python_path']

class {'supervisor':
  supervisor_conf => "/etc/supervisord.conf",
  require => Exec["pip_install_modules"],
}

class {'upstart':
    supervisor_conf => '/etc/init/supervisord.conf',
    rabbitmq_conf => '/etc/init/rabbitmq.conf',
}