# ==============================================================================
# Script R pentru descarcarea populatiei pe UAT-uri din baza de date INSSE
# TEMPO Online, categoria/matricea POP107D:
# "POPULATIA DUPA DOMICILIU la 1 ianuarie pe grupe de varsta si varste,
#  sexe, judete si localitati"
#
# Mod de utilizare:
#   1) Ca functie in R / RStudio:
#      source("transform_data/tempo_pop.r")
#      df_2025 <- descarca_populatie_uat(2025)   # implicit anul 2025
#      df_2024 <- descarca_populatie_uat(2024)   # orice alt an disponibil
#
#   2) Direct din linia de comanda (PowerShell / Terminal):
#      & "C:\Program Files\R\R-4.6.1\bin\Rscript.exe" "transform_data/tempo_pop.r" 2025
#      & "C:\Program Files\R\R-4.6.1\bin\Rscript.exe" "transform_data/tempo_pop.r" 2024
#      (Daca nu se specifica niciun an, se foloseste implicit 2025.)
# ==============================================================================

.configureaza_librarie_r <- function() {
  lib_user <- Sys.getenv("R_LIBS_USER")
  if (nzchar(lib_user)) {
    if (!dir.exists(lib_user)) {
      dir.create(lib_user, recursive = TRUE, showWarnings = FALSE)
    }
    if (dir.exists(lib_user)) {
      .libPaths(unique(c(lib_user, .libPaths())))
    }
  }
  invisible(.libPaths())
}

.asigura_pachete <- function(pachete = c("TEMPO", "writexl")) {
  .configureaza_librarie_r()
  lipsa <- pachete[!vapply(pachete, requireNamespace, logical(1), quietly = TRUE)]
  if (length(lipsa) > 0) {
    message("Instalez pachetele R lipsa: ", paste(lipsa, collapse = ", "), " ...")
    lib_dest <- .libPaths()[1]
    tip_pkg <- if (.Platform$OS.type == "windows") "binary" else getOption("pkgType")
    install.packages(
      lipsa,
      lib = lib_dest,
      repos = c("https://rprojectromania.r-universe.dev", "https://cloud.r-project.org"),
      type = tip_pkg
    )
  }
}

.detecteaza_director_script <- function() {
  args_all <- commandArgs(trailingOnly = FALSE)
  arg_file <- grep("^--file=", args_all, value = TRUE)
  if (length(arg_file) > 0) {
    cale <- sub("^--file=", "", arg_file[1])
    return(dirname(normalizePath(cale, winslash = "/", mustWork = FALSE)))
  }
  NULL
}

.SCRIPT_DIR <- .detecteaza_director_script()

.gaseste_director_raw_data <- function() {
  candidati <- c(
    file.path(getwd(), "raw_data"),
    file.path(dirname(getwd()), "raw_data")
  )
  if (!is.null(.SCRIPT_DIR)) {
    candidati <- c(candidati, file.path(dirname(.SCRIPT_DIR), "raw_data"))
  }
  for (cand in candidati) {
    if (dir.exists(cand)) {
      return(normalizePath(cand, winslash = "/", mustWork = FALSE))
    }
  }
  file.path(getwd(), "raw_data")
}

.normalizeaza_an <- function(an) {
  if (is.null(an) || length(an) == 0) {
    stop("Parametrul `an` nu poate fi gol. Specifica un an (ex: 2025).", call. = FALSE)
  }
  an_txt <- trimws(as.character(an)[1])
  if (is.na(an_txt) || !grepl("\\d{4}", an_txt)) {
    stop("An invalid: '", an_txt, "'. Specifica un an din 4 cifre (ex: 2025).", call. = FALSE)
  }
  as.integer(sub("^.*?(\\d{4}).*$", "\\1", an_txt))
}

#' Descarca populatia totala pe fiecare UAT din toate judetele (matricea POP107D)
#'
#' @param an Anul dorit (numar sau text, ex: 2025, "2025", "Anul 2025"). Implicit 2025.
#' @param cale_iesire_xlsx Calea fisierului Excel de iesire. Implicit `raw_data/populatie_per_uat.xlsx`.
#'   Transmite `FALSE` sau `NA` daca nu doresti scrierea fisierului Excel.
#' @return Un `data.frame` cu coloanele: `Judet`, `SIRUTA_UAT`, `SIRUTA`, `UAT`, `An`, `Populatie`.
descarca_populatie_uat <- function(an = 2025,
                                   cale_iesire_xlsx = NULL) {
  .asigura_pachete(c("TEMPO", "writexl"))

  an_num <- .normalizeaza_an(an)
  eticheta_an <- paste("Anul", an_num)

  message("Interoghez metadatele INSSE TEMPO pentru matricea POP107D...")
  meta <- TEMPO::tempo_meta("POP107D", language = "ro")

  ani_disponibili <- trimws(meta$values$Ani$label)
  if (!(eticheta_an %in% ani_disponibili)) {
    ani_num_disp <- sort(suppressWarnings(as.integer(gsub("[^0-9]", "", ani_disponibili))))
    stop(
      sprintf(
        "Anul %d (%s) nu este disponibil in matricea POP107D. Ani disponibili: %s.",
        an_num, eticheta_an, paste(ani_num_disp, collapse = ", ")
      ),
      call. = FALSE
    )
  }

  judete <- setdiff(trimws(meta$values$Judete$label), "TOTAL")
  localitati <- setdiff(trimws(meta$values$Localitati$label), "TOTAL")

  message(sprintf(
    "Descarc populatia pentru %d judete si %d UAT-uri (anul %d)...",
    length(judete), length(localitati), an_num
  ))

  raw_df <- TEMPO::tempo_get(
    code = "POP107D",
    filters = list(
      "Varste si grupe de varsta" = "Total",
      "Sexe" = "Total",
      "Judete" = judete,
      "Localitati" = localitati,
      "Ani" = eticheta_an
    ),
    language = "ro",
    tidy = TRUE,
    progress = FALSE
  )

  # TEMPO returneaza uneori spatii suplimentare la inceputul/sfarsitul numelor
  judet_curat <- trimws(as.character(raw_df[["Judete"]]))
  siruta_uat <- trimws(as.character(raw_df[["Localitati"]]))
  siruta <- sub("\\s+.*$", "", siruta_uat)
  uat <- trimws(sub("^[0-9]+\\s+", "", siruta_uat))
  an_val <- as.integer(raw_df[["Ani"]])
  populatie <- as.numeric(raw_df[["value"]])

  rezultat <- data.frame(
    Judet = judet_curat,
    SIRUTA_UAT = siruta_uat,
    SIRUTA = siruta,
    UAT = uat,
    An = an_val,
    Populatie = populatie,
    stringsAsFactors = FALSE
  )

  rezultat <- rezultat[
    rezultat$Judet != "TOTAL" & rezultat$SIRUTA_UAT != "TOTAL",
    ,
    drop = FALSE
  ]
  rownames(rezultat) <- NULL

  dir_raw <- .gaseste_director_raw_data()
  if (is.null(cale_iesire_xlsx)) {
    cale_iesire_xlsx <- file.path(dir_raw, "populatie_per_uat.xlsx")
  }

  if (is.character(cale_iesire_xlsx) && length(cale_iesire_xlsx) == 1 && nzchar(cale_iesire_xlsx)) {
    dir.create(dirname(cale_iesire_xlsx), recursive = TRUE, showWarnings = FALSE)
    writexl::write_xlsx(rezultat, path = cale_iesire_xlsx)
    message("Salvat Excel: ", cale_iesire_xlsx)
  }

  message(sprintf(
    "Finalizat: %d UAT-uri din %d judete descarcate pentru anul %d.",
    nrow(rezultat), length(unique(rezultat$Judet)), an_num
  ))

  rezultat
}

# Executie automata cand scriptul este rulat direct cu Rscript
if (!interactive() && sys.nframe() == 0L) {
  args <- commandArgs(trailingOnly = TRUE)
  an_cerut <- if (length(args) >= 1 && nzchar(trimws(args[1]))) args[1] else 2025
  invisible(descarca_populatie_uat(an = an_cerut))
}
