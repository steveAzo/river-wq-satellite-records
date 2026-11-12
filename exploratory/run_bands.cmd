@echo off
rem POST HOC hard-case band sensitivity (second outside review, 2026-11-12). Run from Paper3\. Resumable (per-site outputs).
cd /d "%~dp0.."
echo START bands %date% %time%>> exploratory\run_bands.log
python -I -W ignore exploratory\explore4_bands.py data\clean\usgs rehearsal4_2023 >> exploratory\run_bands.log 2>&1
echo EXIT %errorlevel% bands 2023 %date% %time%>> exploratory\run_bands.log
python -I -W ignore exploratory\explore4_bands.py data\clean\usgs_new3_2024 rehearsal4v2 >> exploratory\run_bands.log 2>&1
echo EXIT %errorlevel% bands 2024 %date% %time%>> exploratory\run_bands.log
python -I -W ignore exploratory\explore4_bands.py data\clean\usgs_new4_2022 confirm4 >> exploratory\run_bands.log 2>&1
echo EXIT %errorlevel% bands 2022 %date% %time%>> exploratory\run_bands.log
echo ALL BANDS DONE>> exploratory\run_bands.log
