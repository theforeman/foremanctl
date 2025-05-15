Name:      rop
Version:   0.0.1
Release:   0%{?dist}
Summary:   Install Foreman using containers

License:   GPL-2-only
URL:       https://github.com/theforeman/foreman-quadlet
Source:    https://github.com/theforeman/foreman-quadlet/releases/download/%{version}/%{name}-%{version}.tar.gz

BuildArch: noarch
Requires:  ansible-collection-theforeman-foreman
Requires:  ansible-collection-theforeman-operations
Requires:  ansible-core
Requires:  python3-obsah

%global _description %{expand:
...}

%description %_description

%prep
%setup -q -n %{name}-%{version}

%build

%install
install -d -m0755 %{buildroot}%{_datadir}/%{name}
install -d -m0755 %{buildroot}%{_bindir}

cp -rf src/* %{buildroot}%{_datadir}/%{name}
cp -rf rop %{buildroot}%{_bindir}/%{name}


%files
%{_bindir}/rop
%{_datadir}/*


%changelog
