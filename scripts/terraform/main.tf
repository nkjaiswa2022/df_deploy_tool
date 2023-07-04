ocals {
    insdatasets = csvdecode(file("${path.root}/../../../deploy/config/${var.build_date}/instance_list.csv"))
}

resource "google_data_fusion_instance" "create_instance" {
  count = length(local.insdatasets)
  name = local.insdatasets[count.index].instance_name
  description = local.insdatasets[count.index].description
  region = local.insdatasets[count.index].region
  type = local.insdatasets[count.index].cdf_version
  enable_stackdriver_logging = true
  enable_stackdriver_monitoring = true
  private_instance = true
  network_config {
    network = local.insdatasets[count.index].cdf_network
    ip_allocation = local.insdatasets[count.index].cdf_ip_range
  }
  version = local.insdatasets[count.index].cdf_release
  dataproc_service_account = local.insdatasets[count.index].default_service_account
}