run "ordinary_valid" {
  command = plan
  variables { public_hostname = "books.example.com" }
}

run "single_char_label" {
  command = plan
  variables { public_hostname = "a.io" }
}

run "label_63" {
  command = plan
  variables { public_hostname = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.com" }
}

run "host_253" {
  command = plan
  variables { public_hostname = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" }
}

run "label_64" {
  command = plan
  variables { public_hostname = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.com" }
  expect_failures = [var.public_hostname]
}

run "host_254" {
  command = plan
  variables { public_hostname = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" }
  expect_failures = [var.public_hostname]
}

run "leading_hyphen" {
  command = plan
  variables { public_hostname = "-a.example.com" }
  expect_failures = [var.public_hostname]
}

run "trailing_hyphen" {
  command = plan
  variables { public_hostname = "a-.example.com" }
  expect_failures = [var.public_hostname]
}

run "empty_label" {
  command = plan
  variables { public_hostname = "a..example.com" }
  expect_failures = [var.public_hostname]
}

run "url" {
  command = plan
  variables { public_hostname = "https://example.com" }
  expect_failures = [var.public_hostname]
}

run "ip" {
  command = plan
  variables { public_hostname = "127.0.0.1" }
  expect_failures = [var.public_hostname]
}

run "wildcard" {
  command = plan
  variables { public_hostname = "*.example.com" }
  expect_failures = [var.public_hostname]
}

run "uppercase" {
  command = plan
  variables { public_hostname = "Books.example.com" }
  expect_failures = [var.public_hostname]
}
