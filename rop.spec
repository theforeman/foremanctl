Name:      rop
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
Requires:  python3-obsah >= 1.1

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

sed -i '/^OBSAH_BASE=/ s|=.\+|=%{_datadir}/%{name}|' rop

%install
install -d -m0755 %{buildroot}%{_datadir}/%{name}
install -d -m0755 %{buildroot}%{_bindir}

cp -r inventories src %{buildroot}%{_datadir}/%{name}
cp -r rop %{buildroot}%{_bindir}/%{name}


%files
%{_bindir}/rop
%{_datadir}/%{name}


%changelog
