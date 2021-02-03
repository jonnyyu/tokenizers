use std::env;

#[cxx::bridge(namespace = "huggingface::tokenizers")]
mod ffi {
    unsafe extern "C++" {
        include!("tokenizers-cpp/tests.h");

        // returns true on success
        pub fn run_tests(data_dir: &str, cli_args: &mut [String]) -> bool;
    }
}

fn main() {
    let mut data_dir = env::current_dir().expect("Don't have a working directory?");
    data_dir.push("../../tokenizers/data");
    if !data_dir.is_dir() {
        panic!("{} should be the directory containing data files, please run `make test` in tokenizers", data_dir.to_string_lossy());
    }
    let mut cli_args: Vec<String> = env::args().collect();
    if !ffi::run_tests(
        data_dir
            .to_str()
            .expect("Working directory is not valid UTF-8"),
        cli_args.as_mut_slice(),
    ) {
        panic!("C++ test suite reported errors");
    }
}
