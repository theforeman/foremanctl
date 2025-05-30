Name:      foremanctl
Version:   0.0.1
Release:   0%{?dist}
Summary:   Install Foreman using containers

License:   GPL-2-only
URL:       https://github.com/theforeman/foreman-quadlet
Source:    https://github.com/theforeman/foreman-quadlet/releases/download/%{version}/%{name}-%{version}.tar.gz

BuildArch: noarch
Requires:  ansible-collection-ansible-posix
Requires:  ansible-collection-community-crypto
Requires:  ansible-collection-community-general
Requires:  ansible-collection-community-postgresql
Requires:  ansible-collection-containers-podman >= 1.14.0
Requires:  ansible-collection-theforeman-foreman
Requires:  python3-obsah >= 1.3

# These are needed on the target host, which is usually localhost
Recommends:  podman
Recommends:  python3-libsemanage
Recommends:  python3-psycopg2

# Tab completion is nice to have
Suggests:  bash-completion
Suggests:  python3-argcomplete

%description
Install Foreman using containers. They are deployed as podman quadlets.

%prep
%setup -q -n %{name}-%{version}

%build
cat > inventories/quadlet <<INVENTORY
[quadlet]
localhost ansible_connection=local
INVENTORY

sed -i '/^OBSAH_BASE=/ s|=.\+|=%{_datadir}/%{name}|' %{name}
sed -i '/^OBSAH_INVENTORY=/ s|=.\+|=%{_sysconfdir}/%{name}/inventory|' %{name}
sed -i '/^OBSAH_STATE=/ s|=.\+|=%{_sharedstatedir}/%{name}|' %{name}
sed -i '/^ANSIBLE_COLLECTIONS_PATH=/ s|=.\+|=%{_datadir}/%{name}/collections|' %{name}

%install
install -d -m0755 %{buildroot}%{_sysconfdir}/%{name}
install -d -m0755 %{buildroot}%{_datadir}/%{name}
install -d -m0755 %{buildroot}%{_bindir}
install -d -m0750 %{buildroot}%{_sharedstatedir}/%{name}

cp inventories/quadlet %{buildroot}%{_sysconfdir}/%{name}/inventory
cp -r src %{buildroot}%{_datadir}/%{name}
cp -r %{name} %{buildroot}%{_bindir}/%{name}


%files
%{_bindir}/%{name}
%{_datadir}/%{name}
%config(noreplace) %{_sysconfdir}/%{name}
%{_sharedstatedir}/%{name}


%changelog
