class Gdsync < Formula
  include Language::Python::Virtualenv

  desc "Sync Google Workspace files from Drive into multiple formats"
  homepage "https://github.com/adamabernathy/gdsync"
  url "https://github.com/adamabernathy/gdsync/archive/refs/tags/v0.1.0.tar.gz"
  sha256 "" # TODO: fill in after first release
  license "MIT"

  depends_on "python@3.12"

  resource "google-api-python-client" do
    url "https://files.pythonhosted.org/packages/source/g/google-api-python-client/google_api_python_client-2.166.0.tar.gz"
    sha256 "" # TODO: fill in
  end

  resource "google-auth" do
    url "https://files.pythonhosted.org/packages/source/g/google-auth/google_auth-2.40.3.tar.gz"
    sha256 "" # TODO: fill in
  end

  resource "google-auth-httplib2" do
    url "https://files.pythonhosted.org/packages/source/g/google-auth-httplib2/google_auth_httplib2-0.2.0.tar.gz"
    sha256 "" # TODO: fill in
  end

  resource "google-auth-oauthlib" do
    url "https://files.pythonhosted.org/packages/source/g/google-auth-oauthlib/google_auth_oauthlib-1.2.1.tar.gz"
    sha256 "" # TODO: fill in
  end

  resource "markdownify" do
    url "https://files.pythonhosted.org/packages/source/m/markdownify/markdownify-0.14.1.tar.gz"
    sha256 "" # TODO: fill in
  end

  resource "pyyaml" do
    url "https://files.pythonhosted.org/packages/source/P/PyYAML/pyyaml-6.0.3.tar.gz"
    sha256 "" # TODO: fill in
  end

  def install
    virtualenv_install_with_resources
  end

  test do
    assert_match version.to_s, shell_output("#{bin}/gdsync --version")
  end
end
