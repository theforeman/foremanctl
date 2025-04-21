# Container Builds

All container images Foreman builds will live at `quay.io/foreman/$service:$tag`.
Dependent services that we do not build ourselves will have a copy of containers stored in Foreman’s quay.io to allow tagging with the Foreman version.

There will be three flavors of Foreman containers:

  * Vanilla Foreman
  * Foreman + Katello
  * Foreman + all plugins

Stage versions of containers will have stage in the name and be published in the Foreman's quay repository:

  * `quay.io/foreman/$service-stage:$tag`

The base image will be `quay.io/centos/centos:stream9`.

## Containerfile Artifacts

Container files will be stored in repositories for each service that mimic packaging.

  * foreman-oci-images
  * pulpcore-oci-images
  * [candlepin-oci-images](https://github.com/theforeman/candlepin-oci-images)

## Container Image Tagging

The tagging rules for release containers images:

  * Project version - X.Y.Z
  * Project version - X.Y
  * Foreman version - X.Y
  * Foreman version - X.Y.Z

The tagging rules for nightly container images:

  * nightly
  * Project version X.Y.Z

