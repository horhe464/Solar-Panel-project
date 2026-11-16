library(TEMPO)
library(writexl)

descarca_populatie_uat <- function(an = 2025) {
  meta <- tempo_meta("POP107D", language = "ro")
  judete <- setdiff(trimws(meta$values$Judete$label), "TOTAL")
  localitati <- setdiff(trimws(meta$values$Localitati$label), "TOTAL")

  raw_df <- tempo_get(
    code = "POP107D",
    filters = list(
      "Varste si grupe de varsta" = "Total",
      "Sexe" = "Total",
      "Judete" = judete,
      "Localitati" = localitati,
      "Ani" = paste("Anul", an)
    ),
    language = "ro",
    tidy = TRUE,
    progress = FALSE
  )

  siruta_uat <- trimws(raw_df$Localitati)
  rezultat <- data.frame(
    Judet = trimws(raw_df$Judete),
    SIRUTA_UAT = siruta_uat,
    SIRUTA = sub("\\s+.*$", "", siruta_uat),
    UAT = trimws(sub("^[0-9]+\\s+", "", siruta_uat)),
    An = as.integer(raw_df$Ani),
    Populatie = as.numeric(raw_df$value)
  )

  write_xlsx(rezultat, "raw_data/populatie_per_uat.xlsx")
  return(rezultat)
}

args <- commandArgs(trailingOnly = TRUE)
an <- if (length(args) >= 1) args[1] else 2025
descarca_populatie_uat(an)
