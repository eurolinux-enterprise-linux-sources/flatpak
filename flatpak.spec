%global flatpak_version 1.0.2
%global flatpak_builder_version 1.0.0
%global ostree_version 2018.8

Name:           flatpak
Version:        %{flatpak_version}
Release:        7%{?dist}
Summary:        Application deployment framework for desktop apps

License:        LGPLv2+
URL:            http://flatpak.org/
Source0:        https://github.com/flatpak/flatpak/releases/download/%{version}/%{name}-%{version}.tar.xz
Source1:        https://github.com/ostreedev/ostree/releases/download/v%{ostree_version}/libostree-%{ostree_version}.tar.xz
Source2:        https://github.com/flatpak/flatpak-builder/releases/download/%{flatpak_builder_version}/flatpak-builder-%{flatpak_builder_version}.tar.xz

# Avoid dbus activating systemd services on the session bus (we don't have a
# user bus, and I'm pretty sure we don't have systemd --user)
Patch0:         no-user-systemd.patch
# Make sure our resulting binaries always have the rpath set to the bundled
# ostree directory
Patch1:         flatpak-ostree-bundle.patch
# https://bugzilla.redhat.com/show_bug.cgi?id=1660137
Patch2:         flatpak-1.0.4-oci-fixes.patch
# https://bugzilla.redhat.com/show_bug.cgi?id=1675435
Patch3:         flatpak-1.0.2-CVE-2019-5736.patch
# https://bugzilla.redhat.com/show_bug.cgi?id=1700652
Patch4:         flatpak-1.0.2-CVE-2019-10063.patch

BuildRequires:  pkgconfig(appstream-glib)
BuildRequires:  pkgconfig(fuse)
BuildRequires:  pkgconfig(gio-unix-2.0)
BuildRequires:  pkgconfig(gobject-introspection-1.0) >= 1.40.0
BuildRequires:  pkgconfig(json-glib-1.0)
BuildRequires:  pkgconfig(libarchive) >= 2.8.0
BuildRequires:  pkgconfig(libelf) >= 0.8.12
BuildRequires:  pkgconfig(libsoup-2.4)
BuildRequires:  pkgconfig(libxml-2.0) >= 2.4
BuildRequires:  pkgconfig(polkit-gobject-1)
BuildRequires:  pkgconfig(libseccomp)
BuildRequires:  pkgconfig(liblzma)
BuildRequires:  pkgconfig(yaml-0.1)
BuildRequires:  pkgconfig(xau)
BuildRequires:  pkgconfig(e2p)
BuildRequires:  automake, autoconf, libtool, gettext-devel, gtk-doc
BuildRequires:  bison
BuildRequires:  docbook-dtds
BuildRequires:  docbook-style-xsl
BuildRequires:  intltool
BuildRequires:  libattr-devel
BuildRequires:  libcap-devel
BuildRequires:  libdwarf-devel
BuildRequires:  gpgme-devel
BuildRequires:  systemd
BuildRequires:  /usr/bin/eu-strip
BuildRequires:  /usr/bin/xmlto
BuildRequires:  /usr/bin/xsltproc
# Bundled ostree BRs:
BuildRequires:  pkgconfig(zlib)
BuildRequires:  pkgconfig(libcurl)
BuildRequires:  openssl-devel
BuildRequires:  pkgconfig(mount)
BuildRequires:  pkgconfig(libsystemd)

# libostree bundling
# https://fedoraproject.org/wiki/EPEL:Packaging_Autoprovides_and_Requires_Filtering
# We're using RPATH to pick up our bundled version
%filter_from_requires /libostree-1/d

# And ensure we don't add a Provides
%{?filter_setup:
%filter_provides_in %{_libdir}/%{name}/.*
%filter_setup
}
# And for now we manually inject this dep; surprisingly the
# command line doesn't currently link to the public libflatpak
# library.
Requires:       %{name}-libs = %{version}-%{release}

# Make sure the document portal is installed
%if 0%{?fedora} || 0%{?rhel} > 7
Recommends:     xdg-desktop-portal > 0.10
# Remove in F30.
Conflicts:      xdg-desktop-portal < 0.10
%else
Requires:       xdg-desktop-portal > 0.10
%endif

%description
flatpak is a system for building, distributing and running sandboxed desktop
applications on Linux. See https://wiki.gnome.org/Projects/SandboxedApps for
more information.

%package builder
# Override to the version of the bundled flatpak-builder.
Version:        %{flatpak_builder_version}
Summary:        Build helper for %{name}
License:        LGPLv2+
# Overridden, as the macro expands to the version of this subpackage.
Requires:       %{name}%{?_isa} = %{flatpak_version}-%{release}
Requires:       /usr/bin/bzip2
Requires:       /usr/bin/bzr
Requires:       /usr/bin/git
Requires:       /usr/bin/patch
Requires:       /usr/bin/strip
Requires:       /usr/bin/svn
Requires:       /usr/bin/tar
Requires:       /usr/bin/unzip

%description builder
flatpak-builder is a tool that makes it easy to build applications and their
dependencies by automating the configure && make && make install steps.

%package devel
# Overriden, to reset the version macro back to that of the base package.
Version:        %{flatpak_version}
Summary:        Development files for %{name}
License:        LGPLv2+
Requires:       %{name}%{?_isa} = %{version}-%{release}
Requires:       %{name}-libs%{?_isa} = %{version}-%{release}

%description devel
This package contains the pkg-config file and development headers for %{name}.

%package libs
Summary:        Libraries for %{name}
License:        LGPLv2+
# Drop if using an external ostree-libs.
Requires:       %{name}%{?_isa} = %{version}-%{release}

%description libs
This package contains libflatpak.


%prep
%setup -q -a 1 -a 2
%patch0 -p1
%patch1 -p1
%patch2 -p1
%patch3 -p1
%patch4 -p1


%build
cd libostree-%{ostree_version}
 %configure \
           --disable-silent-rules \
           --disable-gtk-doc \
           --disable-man \
           --disable-rofiles-fuse \
           --without-libmount \
           --disable-introspection \
           --without-selinux \
           --without-dracut \
           LIBS=-lgpg-error \
           CPPFLAGS="$CPPFLAGS -DDISABLE_OTMPFILE"
%make_build V=1
cd ..

mkdir -p root/lib/pkgconfig
ROOT=`pwd`/root

mv libostree-%{ostree_version}/.libs/libostree-1.so* root/lib
ls -al root/lib/libostree*
ln -s `pwd`/libostree-%{ostree_version}/src/libostree root/include

cat > root/lib/pkgconfig/ostree-1.pc <<EOF
Name: OSTree
Description: Git for operating system binaries
Version: %{ostree_version}
Requires: gio-unix-2.0
Libs: -L$ROOT/lib -Wl,-rpath=%{_libdir}/flatpak -lostree-1
Cflags: -I$ROOT/include
EOF
rm -f configure
gtkdocize
autoreconf -f -i -s
export PKG_CONFIG_PATH=$ROOT/lib/pkgconfig
(if ! test -x configure; then NOCONFIGURE=1 ./autogen.sh; CONFIGFLAGS=--enable-gtk-doc; fi;
 # User namespace support is sufficient.
 # Generate consistent IDs between runs to avoid multilib problems.
 export XMLTO_FLAGS="--stringparam generate.consistent.ids=1"
 %configure \
            --with-priv-mode=none \
            --enable-docbook-docs \
            --disable-introspection $CONFIGFLAGS)
%make_build V=1
sed -i s/ostree-1// %{name}.pc

cd flatpak-builder-%{flatpak_builder_version}
cat > flatpak <<EOF
#!/bin/sh
echo %{flatpak_version}
EOF
chmod +x ./flatpak
 %configure \
           --with-dwarf-header=%{_includedir}/libdwarf \
           --disable-silent-rules \
           FLATPAK=./flatpak
%make_build CFLAGS+=-std=c99 V=1


%install
mkdir -p %{buildroot}%{_datadir}/gtk-doc/html/flatpak
%make_install
install -d %{buildroot}%{_libdir}/flatpak
mv root/lib/libostree-1.so* %{buildroot}%{_libdir}/flatpak
# Work around https://bugzilla.redhat.com/show_bug.cgi?id=1392354
install -d %{buildroot}/%{_pkgdocdir}
if test -d %{buildroot}/%{_docdir}/%{name}; then
    mv %{buildroot}/%{_docdir}/%{name}/* %{buildroot}/%{_pkgdocdir}
    rmdir %{buildroot}/%{_docdir}/%{name}/
fi
install -t %{buildroot}/%{_pkgdocdir} -pm 644 NEWS README.md
# The system repo is not installed by the flatpak build system.
install -d %{buildroot}%{_localstatedir}/lib/flatpak
install -d %{buildroot}%{_sysconfdir}/flatpak/remotes.d
rm -f %{buildroot}%{_libdir}/libflatpak.la
# We don't have python3 and flatpak introspection is disabled
rm %{buildroot}%{_bindir}/flatpak-bisect
rm %{buildroot}%{_bindir}/flatpak-coredumpctl

cd flatpak-builder-%{flatpak_builder_version}
%make_install
cd ..
%find_lang %{name}


%post
# Create an (empty) system-wide repo.
flatpak remote-list --system &> /dev/null || :

%post libs -p /sbin/ldconfig

%postun libs -p /sbin/ldconfig


%files -f %{name}.lang
%license COPYING
# Comply with the packaging guidelines about not mixing relative and absolute
# paths in doc.
%doc %{_pkgdocdir}
%{_bindir}/flatpak
%{_datadir}/bash-completion
%{_datadir}/dbus-1/interfaces/org.freedesktop.Flatpak.xml
%{_datadir}/dbus-1/interfaces/org.freedesktop.portal.Flatpak.xml
%{_datadir}/dbus-1/services/org.freedesktop.Flatpak.service
%{_datadir}/dbus-1/services/org.freedesktop.portal.Flatpak.service
%{_datadir}/dbus-1/system-services/org.freedesktop.Flatpak.SystemHelper.service
# Co-own directory.
%{_datadir}/gdm/env.d
%{_datadir}/%{name}
%{_datadir}/polkit-1/actions/org.freedesktop.Flatpak.policy
%{_datadir}/polkit-1/rules.d/org.freedesktop.Flatpak.rules
%{_datadir}/zsh/site-functions
%{_libexecdir}/flatpak-dbus-proxy
%{_libexecdir}/flatpak-portal
%{_libexecdir}/flatpak-session-helper
%{_libexecdir}/flatpak-system-helper
%attr(04755,root,root) %{_libexecdir}/flatpak-bwrap

%dir %{_localstatedir}/lib/flatpak
%{_mandir}/man1/%{name}*.1*
%{_mandir}/man5/%{name}-metadata.5*
%{_mandir}/man5/flatpak-flatpakref.5*
%{_mandir}/man5/flatpak-flatpakrepo.5*
%{_mandir}/man5/flatpak-installation.5*
%{_mandir}/man5/flatpak-remote.5*
%exclude %{_mandir}/man1/flatpak-builder.1*
%{_sysconfdir}/dbus-1/system.d/org.freedesktop.Flatpak.SystemHelper.conf
%{_sysconfdir}/flatpak/remotes.d
%{_sysconfdir}/profile.d/flatpak.sh
%{_unitdir}/flatpak-system-helper.service
%{_userunitdir}/flatpak-portal.service
%{_userunitdir}/flatpak-session-helper.service
# Co-own directory.
%{_userunitdir}/dbus.service.d

%files builder
%doc %{_docdir}/flatpak-builder
%{_bindir}/flatpak-builder
%{_mandir}/man1/flatpak-builder.1*
%{_mandir}/man5/flatpak-manifest.5*

%files devel
%{_datadir}/gtk-doc/
%{_includedir}/%{name}/
%{_libdir}/libflatpak.so
%{_libdir}/pkgconfig/%{name}.pc

%files libs
%license COPYING
%{_libdir}/flatpak/libostree-1.so*
%{_libdir}/libflatpak.so.*


%changelog
* Mon Apr 29 2019 David King <dking@redhat.com> - 1.0.2-7
- Fix IOCSTI sandbox bypass (#1700652)

* Fri Feb 15 2019 David King <dking@redhat.com> - 1.0.2-6
- Tweak /proc sandbox patch (#1675435)

* Wed Feb 13 2019 David King <dking@redhat.com> - 1.0.2-5
- Do not mount /proc in root sandbox (#1675435)

* Mon Jan 14 2019 David King <dking@redhat.com> - 1.0.2-4
- Apply the OCI support patch (#1660137)

* Mon Jan 07 2019 David King <dking@redhat.com> - 1.0.2-3
- Backport patches to improve OCI support (#1660137)

* Thu Sep 13 2018 Kalev Lember <klember@redhat.com> - 1.0.2-2
- Update to 1.0.2 (#1570030)

* Wed Sep 12 2018 Kalev Lember <klember@redhat.com> - 1.0.1-1
- Update to 1.0.1 (#1570030)

* Mon Jun 04 2018 David King <dking@redhat.com> - 0.10.4-2
- Fix subpackage versions (#1585604)

* Fri Jun 01 2018 David King <dking@redhat.com> - 0.10.4-1
- Rebase to 0.10.4 (#1570030)

* Mon Dec 11 2017 David King <dking@redhat.com> - 0.8.8-3
- Disable O_TMPFILE in libglnx (#1520311)

* Fri Nov 10 2017 Ray Strode <rstrode@redhat.com> - 0.8.8-2
- Fix crasher in xdg-desktop-portal
  Resolves: #1503579
- Tweak spec file so it still builds even though we need to
  autoreconf.

* Wed Nov 01 2017 David King <dking@redhat.com> - 0.8.8-1
- Update to 0.8.8 (#1500800)

* Tue Aug 01 2017 Colin Walters <walters@verbum.org> - 0.8.7-3
- Fix libostree bundling:
  Ensure we do not Provide or Require libostree.
  Move the shared library into flatpak-libs so flatpak always
  depends on it.
  Keep the shared library filename as libostree, but put it
  under a private directory.  Renaming the file on disk did not
  really do much since the dynamic linker and RPM work from the
  soname.
  Resolves: #1476905

* Tue Aug 01 2017 Colin Walters <walters@verbum.org> - 0.8.7-2
- Tweak build to work both with and without BZ#1392354

* Tue Jun 20 2017 Kalev Lember <klember@redhat.com> - 0.8.7-1
- Update to 0.8.7
- Resolves: #1391018

* Tue Apr  4 2017 Alexander Larsson <alexl@redhat.com> - 0.8.5-2
- Add libostree use-after-free patch
- Resolves: #1391018

* Mon Apr 03 2017 Kalev Lember <klember@redhat.com> - 0.8.5-1
- Update to 0.8.5
- Resolves: #1391018

* Fri Mar 10 2017 David King <dking@redhat.com> - 0.8.4-2
- Sync bzip2 dependency with Fedora package
- Make the libs subpackage depend on the base package for libostree
- Fix multilib issues with XML-based documentation

* Fri Mar 10 2017 Kalev Lember <klember@redhat.com> - 0.8.4-1
- Update to 0.8.4
- Resolves: #1391018

* Wed Feb 22 2017 Kalev Lember <klember@redhat.com> - 0.8.3-4
- Remove ExcludeArch ppc now that we have libseccomp there
- Resolves: #1391018

* Fri Feb 17 2017 Alexander Larsson <alexl@redhat.com> - 0.8.3-3
- ExcludeArch 32bit ppc which doesn't have libseccomp
- Resolves: #1391018

* Fri Feb 17 2017 Alexander Larsson <alexl@redhat.com> - 0.8.3-2
- Added pkgconfig(e2p) build dependency
- Resolves: #1391018

* Fri Feb 17 2017 Alexander Larsson <alexl@redhat.com> - 0.8.3-1
- Bundle ostree and bubblewrap
- Resolves: #1391018

* Tue Feb 14 2017 Kalev Lember <klember@redhat.com> - 0.8.3-1
- Update to 0.8.3

* Fri Jan 27 2017 Kalev Lember <klember@redhat.com> - 0.8.2-1
- Update to 0.8.2

* Wed Jan 18 2017 David King <amigadave@amigadave.com> - 0.8.1-1
- Update to 0.8.1

* Tue Dec 20 2016 Kalev Lember <klember@redhat.com> - 0.8.0-1
- Update to 0.8.0

* Tue Nov 29 2016 David King <amigadave@amigadave.com> - 0.6.14-2
- Add a patch to fix a GNOME Software crash
- Silence repository listing during post

* Tue Nov 29 2016 Kalev Lember <klember@redhat.com> - 0.6.14-1
- Update to 0.6.14

* Wed Oct 26 2016 David King <amigadave@amigadave.com> - 0.6.13-2
- Add empty /etc/flatpak/remotes.d

* Tue Oct 25 2016 David King <amigadave@amigadave.com> - 0.6.13-1
- Update to 0.6.13

* Thu Oct 06 2016 David King <amigadave@amigadave.com> - 0.6.12-1
- Update to 0.6.12

* Tue Sep 20 2016 Kalev Lember <klember@redhat.com> - 0.6.11-1
- Update to 0.6.11
- Set minimum ostree and bubblewrap versions

* Mon Sep 12 2016 David King <amigadave@amigadave.com> - 0.6.10-1
- Update to 0.6.10

* Tue Sep 06 2016 David King <amigadave@amigadave.com> - 0.6.9-2
- Look for bwrap in PATH

* Thu Aug 25 2016 David King <amigadave@amigadave.com> - 0.6.9-1
- Update to 0.6.9

* Mon Aug 01 2016 David King <amigadave@amigadave.com> - 0.6.8-1
- Update to 0.6.8 (#1361823)

* Thu Jul 21 2016 David King <amigadave@amigadave.com> - 0.6.7-2
- Use system bubblewrap

* Fri Jul 01 2016 David King <amigadave@amigadave.com> - 0.6.7-1
- Update to 0.6.7

* Thu Jun 23 2016 David King <amigadave@amigadave.com> - 0.6.6-1
- Update to 0.6.6

* Fri Jun 10 2016 David King <amigadave@amigadave.com> - 0.6.5-1
- Update to 0.6.5

* Wed Jun 01 2016 David King <amigadave@amigadave.com> - 0.6.4-1
- Update to 0.6.4

* Tue May 31 2016 David King <amigadave@amigadave.com> - 0.6.3-1
- Update to 0.6.3
- Move bwrap to main package

* Tue May 24 2016 David King <amigadave@amigadave.com> - 0.6.2-1
- Rename from xdg-app to flatpak (#1337434)
