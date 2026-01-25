//! Backend configuration, detection, and installation module.
//!
//! This module handles backend setup **before** the Python bridge is running.
//! All detection and installation happens in pure Rust.

pub mod config;
pub mod detection;
pub mod installer;

pub use config::*;
pub use detection::*;
pub use installer::*;
