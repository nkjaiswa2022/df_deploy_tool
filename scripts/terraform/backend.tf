terraform {
  backend "gcs" {
    bucket  = "cicd-tf-state"
    prefix  = "terraform/state"
  }
}